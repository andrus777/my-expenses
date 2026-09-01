package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.remote.ResponseMapper
import com.andrus.myexpenses.data.remote.StatisticsApi
import com.andrus.myexpenses.domain.model.*
import com.andrus.myexpenses.domain.repository.StatisticsRepository
import java.math.BigDecimal
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope

class DefaultStatisticsRepository(
    private val api: StatisticsApi,
    private val responses: ResponseMapper,
) : StatisticsRepository {
    override suspend fun load(dateFrom: String, dateTo: String, interval: String) = coroutineScope {
        val summary = async { responses.requireBody(api.summary(dateFrom, dateTo)) }
        val categories = async { responses.requireBody(api.categories(dateFrom, dateTo)) }
        val timeline = async { responses.requireBody(api.timeline(dateFrom, dateTo, interval)) }
        val subscriptions = async { responses.requireBody(api.subscriptions()) }
        val summaryDto = summary.await()
        val subscriptionsDto = subscriptions.await()
        StatisticsSnapshot(
            summary = StatisticsSummary(
                BigDecimal(summaryDto.total), summaryDto.operations_count,
                BigDecimal(summaryDto.average_daily), BigDecimal(summaryDto.previous_period_total),
                summaryDto.change_percent?.let(::BigDecimal),
            ),
            categories = categories.await().items.map {
                CategoryStatistic(it.category_name, BigDecimal(it.total), BigDecimal(it.percent))
            },
            timeline = timeline.await().items.map { TimelinePoint(it.period, BigDecimal(it.total)) },
            subscriptions = SubscriptionStatistics(
                BigDecimal(subscriptionsDto.monthly_total), BigDecimal(subscriptionsDto.yearly_total),
                subscriptionsDto.active_count,
            ),
        )
    }
}
