package com.andrus.myexpenses.data.local

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.andrus.myexpenses.domain.model.Expense
import com.andrus.myexpenses.domain.model.SyncStatus

enum class PendingAction { CREATE, UPDATE, DELETE, NONE }

@Entity(
    tableName = "expenses",
    indices = [
        Index(value = ["ownerUserId", "expenseDate"]),
        Index(value = ["ownerUserId", "categoryId"]),
        Index(value = ["ownerUserId", "clientOperationId"], unique = true),
        Index(value = ["serverId"], unique = true),
    ],
)
data class ExpenseEntity(
    @PrimaryKey val localId: String,
    val ownerUserId: String,
    val serverId: String?,
    val categoryId: String,
    val amountMinor: Long,
    val currency: String,
    val expenseDate: String,
    val merchant: String?,
    val description: String?,
    val comment: String?,
    val source: String,
    val clientOperationId: String,
    val createdAt: String,
    val updatedAt: String,
    val syncStatus: String,
    val pendingAction: String,
    val locallyDeleted: Boolean,
)

data class ExpenseWithCategory(
    @androidx.room.Embedded val expense: ExpenseEntity,
    val categoryName: String,
) {
    fun toDomain() = Expense(
        localId = expense.localId,
        serverId = expense.serverId,
        categoryId = expense.categoryId,
        categoryName = categoryName,
        amountMinor = expense.amountMinor,
        currency = expense.currency,
        expenseDate = expense.expenseDate,
        merchant = expense.merchant,
        description = expense.description,
        comment = expense.comment,
        clientOperationId = expense.clientOperationId,
        syncStatus = SyncStatus.valueOf(expense.syncStatus),
    )
}
