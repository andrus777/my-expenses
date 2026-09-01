package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface BudgetApi {
    @GET("budgets") suspend fun list(): Response<BudgetListResponse>
    @POST("budgets") suspend fun create(@Body request: BudgetRequest): Response<BudgetResponse>
    @PATCH("budgets/{id}") suspend fun update(@Path("id") id: String, @Body request: BudgetRequest): Response<BudgetResponse>
    @DELETE("budgets/{id}") suspend fun delete(@Path("id") id: String): Response<Unit>
}
