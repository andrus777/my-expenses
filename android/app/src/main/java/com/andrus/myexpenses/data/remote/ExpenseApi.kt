package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.CategoryListResponse
import com.andrus.myexpenses.data.model.ExpenseListResponse
import com.andrus.myexpenses.data.model.ExpensePatchRequest
import com.andrus.myexpenses.data.model.ExpenseRequest
import com.andrus.myexpenses.data.model.ExpenseResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface ExpenseApi {
    @GET("categories")
    suspend fun categories(): Response<CategoryListResponse>

    @GET("expenses")
    suspend fun expenses(
        @Query("page") page: Int,
        @Query("per_page") perPage: Int = 100,
        @Query("sort") sort: String = "expense_date",
        @Query("order") order: String = "desc",
    ): Response<ExpenseListResponse>

    @POST("expenses")
    suspend fun create(@Body request: ExpenseRequest): Response<ExpenseResponse>

    @PATCH("expenses/{id}")
    suspend fun update(
        @Path("id") id: String,
        @Body request: ExpensePatchRequest,
    ): Response<ExpenseResponse>

    @DELETE("expenses/{id}")
    suspend fun delete(@Path("id") id: String): Response<Unit>
}
