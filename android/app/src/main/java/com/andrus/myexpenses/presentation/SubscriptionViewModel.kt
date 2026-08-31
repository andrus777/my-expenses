package com.andrus.myexpenses.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.andrus.myexpenses.domain.model.*
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import com.andrus.myexpenses.domain.repository.SubscriptionRepository
import java.math.BigDecimal
import java.math.RoundingMode
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class SubscriptionsUiState(
    val subscriptions: List<Subscription> = emptyList(),
    val categories: List<Category> = emptyList(),
    val payments: List<SubscriptionPayment> = emptyList(),
    val loading: Boolean = true,
    val error: String? = null,
)

class SubscriptionViewModel(
    private val repository: SubscriptionRepository,
    expenseRepository: ExpenseRepository,
) : ViewModel() {
    private val loading = MutableStateFlow(true)
    private val error = MutableStateFlow<String?>(null)
    val state = combine(repository.subscriptions, expenseRepository.categories, repository.payments, loading, error) { subscriptions, categories, payments, busy, message ->
        SubscriptionsUiState(subscriptions, categories, payments, busy, message)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), SubscriptionsUiState())

    init { refresh() }

    fun refresh() = launch { repository.refresh() }
    fun pay(id: String) = launch { repository.markPaid(id) }
    fun delete(id: String) = launch { repository.delete(id) }
    fun history(id: String) = launch { repository.loadPayments(id) }

    fun save(id: String?, name: String, amount: String, categoryId: String, frequency: String, interval: String?, nextDate: String): String? {
        if (name.isBlank() || categoryId.isBlank()) return "Заполните название и категорию"
        val minor = runCatching { BigDecimal(amount.replace(',', '.')).setScale(2, RoundingMode.UNNECESSARY).movePointRight(2).longValueExact() }.getOrNull()
        if (minor == null || minor <= 0) return "Введите корректную сумму"
        val custom = if (frequency == "CUSTOM") interval?.toIntOrNull()?.takeIf { it > 0 } ?: return "Укажите интервал" else null
        launch { repository.save(id, SubscriptionDraft(name.trim(), categoryId, minor, frequency, custom, nextDate)) }
        return null
    }

    private fun launch(block: suspend () -> Unit) = viewModelScope.launch {
        loading.value = true
        error.value = null
        runCatching { block() }.onFailure { error.value = it.message ?: "Не удалось выполнить запрос" }
        loading.value = false
    }

    class Factory(private val subscriptions: SubscriptionRepository, private val expenses: ExpenseRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = SubscriptionViewModel(subscriptions, expenses) as T
    }
}
