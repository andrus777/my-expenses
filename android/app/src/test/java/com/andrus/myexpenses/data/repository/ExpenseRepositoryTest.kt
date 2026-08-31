package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.local.CategoryDao
import com.andrus.myexpenses.data.local.ExpenseDao
import com.andrus.myexpenses.data.local.ExpenseEntity
import com.andrus.myexpenses.data.local.PendingAction
import com.andrus.myexpenses.data.model.CategoryDto
import com.andrus.myexpenses.data.model.ExpenseDto
import com.andrus.myexpenses.data.remote.ExpenseRemoteDataSource
import com.andrus.myexpenses.domain.model.ExpenseDraft
import com.andrus.myexpenses.domain.model.SyncStatus
import com.andrus.myexpenses.domain.repository.SyncScheduler
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import io.mockk.slot
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class ExpenseRepositoryTest {
    private val expenseDao = mockk<ExpenseDao>(relaxed = true)
    private val categoryDao = mockk<CategoryDao>(relaxed = true)
    private val remote = mockk<ExpenseRemoteDataSource>()
    private val scheduler = mockk<SyncScheduler>(relaxed = true)

    @Test
    fun `add persists pending expense before scheduling sync`() = runTest {
        val captured = slot<ExpenseEntity>()
        coEvery { expenseDao.upsert(capture(captured)) } returns Unit
        val repository = repository()

        val localId = repository.add(ExpenseDraft("category", 125050, "2026-08-31"))

        assertEquals(localId, captured.captured.localId)
        assertEquals(SyncStatus.PENDING_SYNC.name, captured.captured.syncStatus)
        assertEquals(PendingAction.CREATE.name, captured.captured.pendingAction)
        assertNotEquals(localId, captured.captured.clientOperationId)
        io.mockk.verify(exactly = 1) { scheduler.schedule() }
    }

    @Test
    fun `idempotent create retry keeps client operation id and reconciles server id`() = runTest {
        val pending = pendingExpense()
        val server = serverExpense(pending.clientOperationId)
        coEvery { remote.categories() } returns listOf(CategoryDto("category", "Еда", true))
        coEvery { expenseDao.pending("user-id") } returns listOf(pending)
        coEvery { remote.create(any()) } returns server
        coEvery { remote.allExpenses() } returns listOf(server)
        coEvery { expenseDao.findByOperation("user-id", pending.clientOperationId) } returns pending
        coEvery { expenseDao.synced("user-id") } returns emptyList()
        val repository = repository()

        repository.sync()
        repository.sync()

        coVerify(exactly = 2) {
            remote.create(match { it.client_operation_id == pending.clientOperationId })
        }
        coVerify(atLeast = 2) {
            expenseDao.upsert(match {
                it.localId == pending.localId && it.serverId == server.id &&
                    it.syncStatus == SyncStatus.SYNCED.name
            })
        }
    }

    private fun repository() = DefaultExpenseRepository(
        expenseDao,
        categoryDao,
        remote,
        flowOf("user-id"),
        scheduler,
    )
}

internal fun pendingExpense() = ExpenseEntity(
    localId = "local-id",
    ownerUserId = "user-id",
    serverId = null,
    categoryId = "category",
    amountMinor = 125050,
    currency = "RUB",
    expenseDate = "2026-08-31",
    merchant = null,
    description = null,
    comment = null,
    source = "MANUAL",
    clientOperationId = "operation-id",
    createdAt = "2026-08-31T00:00:00Z",
    updatedAt = "2026-08-31T00:00:00Z",
    syncStatus = SyncStatus.PENDING_SYNC.name,
    pendingAction = PendingAction.CREATE.name,
    locallyDeleted = false,
)

internal fun serverExpense(operationId: String) = ExpenseDto(
    id = "server-id",
    category_id = "category",
    amount = "1250.50",
    currency = "RUB",
    expense_date = "2026-08-31",
    merchant = null,
    description = null,
    comment = null,
    source = "MANUAL",
    client_operation_id = operationId,
    created_at = "2026-08-31T00:00:00Z",
    updated_at = "2026-08-31T00:00:00Z",
)
