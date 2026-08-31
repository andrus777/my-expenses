package com.andrus.myexpenses.domain.model

enum class SyncStatus { PENDING_SYNC, SYNCED, SYNC_ERROR }

data class Expense(
    val localId: String,
    val serverId: String?,
    val categoryId: String,
    val categoryName: String,
    val amountMinor: Long,
    val currency: String,
    val expenseDate: String,
    val merchant: String?,
    val description: String?,
    val comment: String?,
    val clientOperationId: String,
    val syncStatus: SyncStatus,
)

data class Category(val id: String, val name: String)

data class ExpenseDraft(
    val categoryId: String,
    val amountMinor: Long,
    val expenseDate: String,
    val merchant: String? = null,
    val description: String? = null,
    val comment: String? = null,
)
