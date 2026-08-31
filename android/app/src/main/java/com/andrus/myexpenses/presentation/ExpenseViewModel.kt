package com.andrus.myexpenses.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.andrus.myexpenses.domain.model.Category
import com.andrus.myexpenses.domain.model.Expense
import com.andrus.myexpenses.domain.model.ExpenseDraft
import com.andrus.myexpenses.domain.model.SyncStatus
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import java.math.BigDecimal
import java.math.RoundingMode
import java.time.LocalDate
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class ExpensesUiState(
    val expenses: List<Expense> = emptyList(),
    val categories: List<Category> = emptyList(),
    val pendingCount: Int = 0,
    val errorCount: Int = 0,
)

class ExpenseViewModel(private val repository: ExpenseRepository) : ViewModel() {
    val state: StateFlow<ExpensesUiState> = combine(repository.expenses, repository.categories) { expenses, categories ->
        ExpensesUiState(
            expenses = expenses,
            categories = categories,
            pendingCount = expenses.count { it.syncStatus == SyncStatus.PENDING_SYNC },
            errorCount = expenses.count { it.syncStatus == SyncStatus.SYNC_ERROR },
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ExpensesUiState())

    init {
        repository.requestSync()
    }

    fun save(localId: String?, amount: String, categoryId: String, date: String = LocalDate.now().toString()): String? {
        val minor = amount.toMinorUnits() ?: return "Введите корректную сумму больше нуля"
        if (categoryId.isBlank()) return "Выберите категорию"
        viewModelScope.launch {
            val draft = ExpenseDraft(categoryId = categoryId, amountMinor = minor, expenseDate = date)
            if (localId == null) repository.add(draft) else repository.update(localId, draft)
        }
        return null
    }

    fun delete(localId: String) = viewModelScope.launch { repository.delete(localId) }

    fun retry(localId: String) = viewModelScope.launch { repository.retry(localId) }

    fun refresh() = repository.requestSync()

    class Factory(private val repository: ExpenseRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = ExpenseViewModel(repository) as T
    }
}

private fun String.toMinorUnits(): Long? = runCatching {
    val value = BigDecimal(trim().replace(',', '.')).setScale(2, RoundingMode.UNNECESSARY)
    value.takeIf { it > BigDecimal.ZERO }?.movePointRight(2)?.longValueExact()
}.getOrNull()
