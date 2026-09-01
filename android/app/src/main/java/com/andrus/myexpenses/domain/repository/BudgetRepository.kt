package com.andrus.myexpenses.domain.repository

import com.andrus.myexpenses.domain.model.Budget
import com.andrus.myexpenses.domain.model.BudgetDraft
import kotlinx.coroutines.flow.StateFlow

interface BudgetRepository {
    val budgets: StateFlow<List<Budget>>
    suspend fun refresh()
    suspend fun save(id: String?, draft: BudgetDraft)
    suspend fun delete(id: String)
}
