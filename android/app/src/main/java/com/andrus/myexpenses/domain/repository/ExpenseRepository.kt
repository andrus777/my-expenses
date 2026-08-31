package com.andrus.myexpenses.domain.repository

import com.andrus.myexpenses.domain.model.Category
import com.andrus.myexpenses.domain.model.Expense
import com.andrus.myexpenses.domain.model.ExpenseDraft
import kotlinx.coroutines.flow.Flow

enum class SyncOutcome { SUCCESS, RETRY }

interface ExpenseRepository {
    val expenses: Flow<List<Expense>>
    val categories: Flow<List<Category>>

    suspend fun add(draft: ExpenseDraft): String
    suspend fun update(localId: String, draft: ExpenseDraft)
    suspend fun delete(localId: String)
    suspend fun retry(localId: String)
    suspend fun sync(): SyncOutcome
    fun requestSync()
}

fun interface SyncScheduler {
    fun schedule()
}
