package com.andrus.myexpenses.presentation

import com.andrus.myexpenses.MainDispatcherRule
import com.andrus.myexpenses.domain.model.*
import com.andrus.myexpenses.domain.repository.BudgetRepository
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class BudgetViewModelTest {
    @get:Rule val dispatcherRule = MainDispatcherRule()

    @Test
    fun `threshold business rule has exact boundaries`() {
        assertEquals(BudgetLevel.NORMAL, budgetLevel(79.99))
        assertEquals(BudgetLevel.WARNING, budgetLevel(80.0))
        assertEquals(BudgetLevel.WARNING, budgetLevel(99.99))
        assertEquals(BudgetLevel.EXCEEDED, budgetLevel(100.0))
    }

    @Test
    fun `invalid dates are rejected without save`() = runTest {
        val budgets = FakeBudgetRepository()
        val viewModel = BudgetViewModel(budgets, expenseRepository())
        advanceUntilIdle()

        val error = viewModel.save(null, "category", "1000", "MONTH", "2026-10-01", "2026-09-01")

        assertEquals("Введите корректный период", error)
        assertEquals(0, budgets.saves)
    }

    @Test
    fun `reached threshold exposes display event`() = runTest {
        val budgets = FakeBudgetRepository()
        budgets.state.value = listOf(budget(setOf(80)))
        val viewModel = BudgetViewModel(budgets, expenseRepository())
        advanceUntilIdle()

        assertEquals("Использовано 80% бюджета «Продукты»", viewModel.state.value.thresholdEvent)
    }
}

private class FakeBudgetRepository : BudgetRepository {
    val state = MutableStateFlow<List<Budget>>(emptyList())
    override val budgets = state
    var saves = 0
    override suspend fun refresh() = Unit
    override suspend fun save(id: String?, draft: BudgetDraft) { saves++ }
    override suspend fun delete(id: String) = Unit
}

private fun expenseRepository(): ExpenseRepository = mockk(relaxed = true) {
    every { categories } returns flowOf(emptyList())
    every { expenses } returns flowOf(emptyList())
}

private fun budget(thresholds: Set<Int>) = Budget(
    "id", "category", "Продукты", 100_000, "RUB", "MONTH", "2026-09-01", "2026-09-30",
    80_000, 20_000, 80.0, thresholds,
)
