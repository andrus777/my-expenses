package com.andrus.myexpenses.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.andrus.myexpenses.domain.model.*
import com.andrus.myexpenses.domain.repository.BudgetRepository
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import java.math.BigDecimal
import java.math.RoundingMode
import java.time.LocalDate
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class BudgetsUiState(
    val budgets: List<Budget> = emptyList(),
    val categories: List<Category> = emptyList(),
    val loading: Boolean = true,
    val error: String? = null,
) {
    val thresholdEvent: String? get() {
        val exceeded = budgets.firstOrNull { 100 in it.thresholdsReached }
        if (exceeded != null) return "Бюджет «${exceeded.categoryName}» исчерпан"
        val warning = budgets.firstOrNull { 80 in it.thresholdsReached }
        return warning?.let { "Использовано 80% бюджета «${it.categoryName}»" }
    }
}

class BudgetViewModel(private val repository: BudgetRepository, expenses: ExpenseRepository) : ViewModel() {
    private val loading = MutableStateFlow(true)
    private val error = MutableStateFlow<String?>(null)
    val state = combine(repository.budgets, expenses.categories, loading, error) { budgets, categories, busy, message ->
        BudgetsUiState(budgets, categories, busy, message)
    }.stateIn(viewModelScope, SharingStarted.Eagerly, BudgetsUiState())

    init { refresh() }
    fun refresh() = launch { repository.refresh() }
    fun delete(id: String) = launch { repository.delete(id) }

    fun save(id: String?, categoryId: String, amount: String, period: String, start: String, end: String): String? {
        if (categoryId.isBlank()) return "Выберите категорию"
        val minor = runCatching { BigDecimal(amount.replace(',', '.')).setScale(2, RoundingMode.UNNECESSARY).movePointRight(2).longValueExact() }.getOrNull()
        if (minor == null || minor <= 0) return "Введите корректную сумму"
        val from = runCatching { LocalDate.parse(start) }.getOrNull()
        val to = runCatching { LocalDate.parse(end) }.getOrNull()
        if (from == null || to == null || from > to) return "Введите корректный период"
        if (period !in setOf("WEEK", "MONTH", "YEAR", "CUSTOM")) return "Выберите период"
        launch { repository.save(id, BudgetDraft(categoryId, minor, period, start, end)) }
        return null
    }

    private fun launch(block: suspend () -> Unit) = viewModelScope.launch {
        loading.value = true
        error.value = null
        runCatching { block() }.onFailure { error.value = it.message ?: "Не удалось выполнить запрос" }
        loading.value = false
    }

    class Factory(private val budgets: BudgetRepository, private val expenses: ExpenseRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = BudgetViewModel(budgets, expenses) as T
    }
}
