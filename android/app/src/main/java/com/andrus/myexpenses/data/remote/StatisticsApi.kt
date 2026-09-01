package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.*
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Query

interface StatisticsApi {
    @GET("statistics/summary")
    suspend fun summary(@Query("date_from") from: String, @Query("date_to") to: String): Response<StatisticsSummaryDto>

    @GET("statistics/categories")
    suspend fun categories(@Query("date_from") from: String, @Query("date_to") to: String): Response<CategoryStatisticsDto>

    @GET("statistics/timeline")
    suspend fun timeline(
        @Query("date_from") from: String,
        @Query("date_to") to: String,
        @Query("interval") interval: String,
    ): Response<TimelineStatisticsDto>

    @GET("statistics/subscriptions")
    suspend fun subscriptions(): Response<SubscriptionStatisticsDto>
}
