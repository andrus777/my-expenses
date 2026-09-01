package com.andrus.myexpenses.presentation

import com.andrus.myexpenses.MainDispatcherRule
import com.andrus.myexpenses.domain.model.*
import com.andrus.myexpenses.domain.repository.StatisticsRepository
import java.math.BigDecimal
import java.time.LocalDate
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class StatisticsViewModelTest {
    @get:Rule val dispatcherRule = MainDispatcherRule()

    @Test
    fun `month period has deterministic calendar boundaries`() = runTest {
        val repository = FakeStatisticsRepository(snapshot())
        val viewModel = StatisticsViewModel(repository) { LocalDate.of(2024, 2, 29) }
        advanceUntilIdle()

        assertEquals("2024-02-01", repository.from)
        assertEquals("2024-02-29", repository.to)
        assertEquals("day", repository.interval)
        assertFalse(viewModel.state.value.loading)
    }

    @Test
    fun `empty snapshot exposes empty state`() = runTest {
        val viewModel = StatisticsViewModel(FakeStatisticsRepository(snapshot(operations = 0))) {
            LocalDate.of(2026, 9, 1)
        }
        advanceUntilIdle()
        assertTrue(viewModel.state.value.empty)
        assertNull(viewModel.state.value.error)
    }

    @Test
    fun `custom invalid range does not call repository`() = runTest {
        val repository = FakeStatisticsRepository(snapshot())
        val viewModel = StatisticsViewModel(repository) { LocalDate.of(2026, 9, 1) }
        advanceUntilIdle()
        val callsBefore = repository.calls

        val error = viewModel.loadCustom("2026-09-02", "2026-09-01")

        assertNotNull(error)
        assertEquals(callsBefore, repository.calls)
    }
}

private class FakeStatisticsRepository(private val result: StatisticsSnapshot) : StatisticsRepository {
    var from = ""
    var to = ""
    var interval = ""
    var calls = 0
    override suspend fun load(dateFrom: String, dateTo: String, interval: String): StatisticsSnapshot {
        calls++
        from = dateFrom
        to = dateTo
        this.interval = interval
        return result
    }
}

private fun snapshot(operations: Int = 1) = StatisticsSnapshot(
    StatisticsSummary(BigDecimal.TEN, operations, BigDecimal.ONE, BigDecimal.ZERO, null),
    emptyList(), emptyList(), SubscriptionStatistics(BigDecimal.ZERO, BigDecimal.ZERO, 0),
)
