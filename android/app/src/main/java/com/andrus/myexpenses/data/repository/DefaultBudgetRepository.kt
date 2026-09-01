package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.model.*
import com.andrus.myexpenses.data.remote.BudgetApi
import com.andrus.myexpenses.data.remote.ResponseMapper
import com.andrus.myexpenses.domain.model.*
import com.andrus.myexpenses.domain.repository.BudgetRepository
import java.math.BigDecimal
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class DefaultBudgetRepository(
    private val api: BudgetApi,
    private val responses: ResponseMapper,
) : BudgetRepository {
    private val mutableBudgets = MutableStateFlow<List<Budget>>(emptyList())
    override val budgets = mutableBudgets.asStateFlow()

    override suspend fun refresh() {
        mutableBudgets.value = responses.requireBody(api.list()).items.map { it.domain() }
    }

    override suspend fun save(id: String?, draft: BudgetDraft) {
        val request = BudgetRequest(
            draft.categoryId, BigDecimal.valueOf(draft.amountMinor, 2).toPlainString(),
            period = draft.period, start_date = draft.startDate, end_date = draft.endDate,
        )
        if (id == null) responses.requireBody(api.create(request)) else responses.requireBody(api.update(id, request))
        refresh()
    }

    override suspend fun delete(id: String) {
        val response = api.delete(id)
        if (!response.isSuccessful) responses.requireBody(response)
        refresh()
    }
}

private fun BudgetDto.domain() = Budget(
    id, category_id, category_name, amount.minor(), currency, period, start_date, end_date,
    spent.minor(), remaining.minor(), usage_percent.toDouble(), thresholds_reached.toSet(),
)

private fun String.minor() = BigDecimal(this).movePointRight(2).longValueExact()
