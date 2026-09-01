package com.andrus.myexpenses.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.andrus.myexpenses.domain.model.StatisticsSnapshot
import com.andrus.myexpenses.domain.repository.StatisticsRepository
import java.time.LocalDate
import java.time.temporal.TemporalAdjusters
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class StatisticsPeriod { WEEK, MONTH, YEAR, CUSTOM }

data class StatisticsUiState(
    val period: StatisticsPeriod = StatisticsPeriod.MONTH,
    val dateFrom: String = "",
    val dateTo: String = "",
    val loading: Boolean = true,
    val data: StatisticsSnapshot? = null,
    val error: String? = null,
) {
    val empty get() = !loading && error == null && data?.summary?.operationsCount == 0
}

class StatisticsViewModel(
    private val repository: StatisticsRepository,
    private val today: () -> LocalDate = LocalDate::now,
) : ViewModel() {
    private val mutableState = MutableStateFlow(StatisticsUiState())
    val state = mutableState.asStateFlow()

    init { selectPeriod(StatisticsPeriod.MONTH) }

    fun selectPeriod(period: StatisticsPeriod) {
        val now = today()
        val from = when (period) {
            StatisticsPeriod.WEEK -> now.minusDays(6)
            StatisticsPeriod.MONTH -> now.with(TemporalAdjusters.firstDayOfMonth())
            StatisticsPeriod.YEAR -> now.with(TemporalAdjusters.firstDayOfYear())
            StatisticsPeriod.CUSTOM -> return mutableState.value.let {
                mutableState.value = it.copy(period = period, loading = false)
            }
        }
        load(period, from.toString(), now.toString())
    }

    fun loadCustom(from: String, to: String): String? {
        val start = runCatching { LocalDate.parse(from) }.getOrNull()
        val end = runCatching { LocalDate.parse(to) }.getOrNull()
        if (start == null || end == null || start > end) return "Введите корректный период"
        load(StatisticsPeriod.CUSTOM, from, to)
        return null
    }

    fun retry() = mutableState.value.let { load(it.period, it.dateFrom, it.dateTo) }

    private fun load(period: StatisticsPeriod, from: String, to: String) = viewModelScope.launch {
        mutableState.value = mutableState.value.copy(period = period, dateFrom = from, dateTo = to, loading = true, error = null)
        runCatching { repository.load(from, to, interval(from, to)) }
            .onSuccess { mutableState.value = mutableState.value.copy(loading = false, data = it) }
            .onFailure {
                mutableState.value = mutableState.value.copy(
                    loading = false, data = null,
                    error = it.message ?: "Не удалось загрузить статистику",
                )
            }
    }

    private fun interval(from: String, to: String): String {
        val days = java.time.temporal.ChronoUnit.DAYS.between(LocalDate.parse(from), LocalDate.parse(to)) + 1
        return if (days <= 31) "day" else if (days <= 180) "week" else "month"
    }

    class Factory(private val repository: StatisticsRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = StatisticsViewModel(repository) as T
    }
}
