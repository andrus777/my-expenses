package com.andrus.myexpenses.domain.model

import java.math.BigDecimal

data class StatisticsSummary(
    val total: BigDecimal,
    val operationsCount: Int,
    val averageDaily: BigDecimal,
    val previousTotal: BigDecimal,
    val changePercent: BigDecimal?,
)

data class CategoryStatistic(val name: String, val total: BigDecimal, val percent: BigDecimal)
data class TimelinePoint(val period: String, val total: BigDecimal)
data class SubscriptionStatistics(val monthlyTotal: BigDecimal, val yearlyTotal: BigDecimal, val activeCount: Int)

data class StatisticsSnapshot(
    val summary: StatisticsSummary,
    val categories: List<CategoryStatistic>,
    val timeline: List<TimelinePoint>,
    val subscriptions: SubscriptionStatistics,
)
