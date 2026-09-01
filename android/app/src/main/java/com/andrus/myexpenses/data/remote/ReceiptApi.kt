package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.ExpenseResponse
import com.andrus.myexpenses.data.model.ReceiptFinalizeRequest
import com.andrus.myexpenses.data.model.ReceiptJobCreated
import com.andrus.myexpenses.data.model.ReceiptJobDto
import com.andrus.myexpenses.data.model.ReceiptJobRequest
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface ReceiptApi {
    @POST("receipts") suspend fun create(@Body body: ReceiptJobRequest): Response<ReceiptJobCreated>
    @GET("receipts/jobs/{id}") suspend fun job(@Path("id") id: String): Response<ReceiptJobDto>
    @POST("receipts/{id}/finalize") suspend fun finalize(
        @Path("id") id: String,
        @Body body: ReceiptFinalizeRequest,
    ): Response<ExpenseResponse>
}
