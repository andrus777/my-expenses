package com.andrus.myexpenses.domain.repository

import com.andrus.myexpenses.domain.model.StatisticsSnapshot

interface StatisticsRepository {
    suspend fun load(dateFrom: String, dateTo: String, interval: String): StatisticsSnapshot
}
