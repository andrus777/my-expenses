package com.andrus.myexpenses.data.model

data class StatisticsSummaryDto(
    val date_from: String,
    val date_to: String,
    val currency: String,
    val total: String,
    val operations_count: Int,
    val average_daily: String,
    val previous_period_total: String,
    val change_percent: String?,
)

data class CategoryStatisticDto(
    val category_id: String,
    val category_name: String,
    val total: String,
    val operations_count: Int,
    val percent: String,
)

data class CategoryStatisticsDto(val currency: String, val items: List<CategoryStatisticDto>)
data class TimelinePointDto(val period: String, val total: String, val operations_count: Int)
data class TimelineStatisticsDto(val interval: String, val currency: String, val items: List<TimelinePointDto>)
data class SubscriptionStatisticsDto(
    val currency: String,
    val monthly_total: String,
    val yearly_total: String,
    val active_count: Int,
)
