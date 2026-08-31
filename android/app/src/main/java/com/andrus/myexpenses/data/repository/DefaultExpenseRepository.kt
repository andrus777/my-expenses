package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.local.CategoryDao
import com.andrus.myexpenses.data.local.CategoryEntity
import com.andrus.myexpenses.data.local.ExpenseDao
import com.andrus.myexpenses.data.local.ExpenseEntity
import com.andrus.myexpenses.data.local.PendingAction
import com.andrus.myexpenses.data.model.ExpenseDto
import com.andrus.myexpenses.data.model.ExpensePatchRequest
import com.andrus.myexpenses.data.model.ExpenseRequest
import com.andrus.myexpenses.data.remote.ApiException
import com.andrus.myexpenses.data.remote.ExpenseRemoteDataSource
import com.andrus.myexpenses.domain.model.ExpenseDraft
import com.andrus.myexpenses.domain.model.SyncStatus
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import com.andrus.myexpenses.domain.repository.SyncOutcome
import com.andrus.myexpenses.domain.repository.SyncScheduler
import java.io.IOException
import java.math.BigDecimal
import java.time.Instant
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map

@OptIn(ExperimentalCoroutinesApi::class)
class DefaultExpenseRepository(
    private val expenseDao: ExpenseDao,
    private val categoryDao: CategoryDao,
    private val remote: ExpenseRemoteDataSource,
    private val currentUserId: Flow<String?>,
    private val scheduler: SyncScheduler,
) : ExpenseRepository {
    override val expenses = currentUserId.flatMapLatest { ownerId ->
        if (ownerId == null) flowOf(emptyList()) else expenseDao.observeVisible(ownerId)
            .map { rows -> rows.map { it.toDomain() } }
    }
    override val categories = currentUserId.flatMapLatest { ownerId ->
        if (ownerId == null) flowOf(emptyList()) else categoryDao.observe(ownerId)
            .map { rows -> rows.map { it.toDomain() } }
    }

    override suspend fun add(draft: ExpenseDraft): String {
        require(draft.amountMinor > 0)
        val ownerId = requireOwner()
        val now = Instant.now().toString()
        val localId = UUID.randomUUID().toString()
        expenseDao.upsert(
            ExpenseEntity(
                localId = localId,
                ownerUserId = ownerId,
                serverId = null,
                categoryId = draft.categoryId,
                amountMinor = draft.amountMinor,
                currency = "RUB",
                expenseDate = draft.expenseDate,
                merchant = draft.merchant,
                description = draft.description,
                comment = draft.comment,
                source = "MANUAL",
                clientOperationId = UUID.randomUUID().toString(),
                createdAt = now,
                updatedAt = now,
                syncStatus = SyncStatus.PENDING_SYNC.name,
                pendingAction = PendingAction.CREATE.name,
                locallyDeleted = false,
            ),
        )
        scheduler.schedule()
        return localId
    }

    override suspend fun update(localId: String, draft: ExpenseDraft) {
        require(draft.amountMinor > 0)
        val current = expenseDao.find(localId, requireOwner()) ?: return
        val action = if (current.pendingAction == PendingAction.CREATE.name) PendingAction.CREATE else PendingAction.UPDATE
        expenseDao.upsert(
            current.copy(
                categoryId = draft.categoryId,
                amountMinor = draft.amountMinor,
                expenseDate = draft.expenseDate,
                merchant = draft.merchant,
                description = draft.description,
                comment = draft.comment,
                updatedAt = Instant.now().toString(),
                syncStatus = SyncStatus.PENDING_SYNC.name,
                pendingAction = action.name,
            ),
        )
        scheduler.schedule()
    }

    override suspend fun delete(localId: String) {
        val current = expenseDao.find(localId, requireOwner()) ?: return
        if (current.serverId == null && current.pendingAction == PendingAction.CREATE.name) {
            expenseDao.deletePermanently(localId)
        } else {
            expenseDao.upsert(
                current.copy(
                    locallyDeleted = true,
                    syncStatus = SyncStatus.PENDING_SYNC.name,
                    pendingAction = PendingAction.DELETE.name,
                    updatedAt = Instant.now().toString(),
                ),
            )
            scheduler.schedule()
        }
    }

    override suspend fun retry(localId: String) {
        val current = expenseDao.find(localId, requireOwner()) ?: return
        val action = when {
            current.serverId == null -> PendingAction.CREATE
            current.locallyDeleted -> PendingAction.DELETE
            else -> PendingAction.UPDATE
        }
        expenseDao.upsert(current.copy(syncStatus = SyncStatus.PENDING_SYNC.name, pendingAction = action.name))
        scheduler.schedule()
    }

    override suspend fun sync(): SyncOutcome {
        val ownerId = currentUserId.first() ?: return SyncOutcome.SUCCESS
        return try {
            refreshCategories(ownerId)
            expenseDao.pending(ownerId).forEach { syncPending(it) }
            pullExpenses(ownerId)
            SyncOutcome.SUCCESS
        } catch (error: Throwable) {
            if (error is CancellationException) throw error
            if (error.isTransient()) SyncOutcome.RETRY else SyncOutcome.SUCCESS
        }
    }

    override fun requestSync() = scheduler.schedule()

    private suspend fun refreshCategories(ownerId: String) {
        val categories = remote.categories().map { CategoryEntity(ownerId, it.id, it.name, it.is_system) }
        categoryDao.clear(ownerId)
        categoryDao.upsertAll(categories)
    }

    private suspend fun syncPending(local: ExpenseEntity) {
        try {
            when (PendingAction.valueOf(local.pendingAction)) {
                PendingAction.CREATE -> reconcile(local, remote.create(local.toCreateRequest()))
                PendingAction.UPDATE -> reconcile(local, remote.update(requireNotNull(local.serverId), local.toPatchRequest()))
                PendingAction.DELETE -> {
                    remote.delete(requireNotNull(local.serverId))
                    expenseDao.deletePermanently(local.localId)
                }
                PendingAction.NONE -> Unit
            }
        } catch (error: Throwable) {
            if (error is CancellationException) throw error
            if (error.isTransient()) throw error
            expenseDao.upsert(
                local.copy(
                    syncStatus = SyncStatus.SYNC_ERROR.name,
                    pendingAction = PendingAction.NONE.name,
                ),
            )
        }
    }

    private suspend fun pullExpenses(ownerId: String) {
        val remoteExpenses = remote.allExpenses()
        val remoteIds = remoteExpenses.mapTo(mutableSetOf()) { it.id }
        remoteExpenses.forEach { dto ->
            val existing = expenseDao.findByOperation(ownerId, dto.client_operation_id)
            if (existing == null || existing.pendingAction == PendingAction.NONE.name) {
                expenseDao.upsert(dto.toEntity(ownerId, existing?.localId ?: dto.client_operation_id))
            }
        }
        expenseDao.synced(ownerId).filter { it.serverId !in remoteIds }.forEach {
            expenseDao.deletePermanently(it.localId)
        }
    }

    private suspend fun reconcile(local: ExpenseEntity, dto: ExpenseDto) {
        expenseDao.upsert(dto.toEntity(local.ownerUserId, local.localId))
    }

    private suspend fun requireOwner() = currentUserId.first() ?: error("Пользователь не авторизован")
}

private fun ExpenseEntity.toCreateRequest() = ExpenseRequest(
    category_id = categoryId,
    amount = amountMinor.asAmount(),
    currency = currency,
    expense_date = expenseDate,
    merchant = merchant,
    description = description,
    comment = comment,
    source = source,
    client_operation_id = clientOperationId,
)

private fun ExpenseEntity.toPatchRequest() = ExpensePatchRequest(
    category_id = categoryId,
    amount = amountMinor.asAmount(),
    currency = currency,
    expense_date = expenseDate,
    merchant = merchant,
    description = description,
    comment = comment,
)

private fun ExpenseDto.toEntity(ownerId: String, localId: String) = ExpenseEntity(
    localId = localId,
    ownerUserId = ownerId,
    serverId = id,
    categoryId = category_id,
    amountMinor = BigDecimal(amount).movePointRight(2).longValueExact(),
    currency = currency,
    expenseDate = expense_date,
    merchant = merchant,
    description = description,
    comment = comment,
    source = source,
    clientOperationId = client_operation_id,
    createdAt = created_at,
    updatedAt = updated_at,
    syncStatus = SyncStatus.SYNCED.name,
    pendingAction = PendingAction.NONE.name,
    locallyDeleted = false,
)

private fun Long.asAmount() = BigDecimal.valueOf(this, 2).toPlainString()

private fun Throwable.isTransient() =
    this is IOException || (this is ApiException && (status == 408 || status == 429 || status >= 500))
