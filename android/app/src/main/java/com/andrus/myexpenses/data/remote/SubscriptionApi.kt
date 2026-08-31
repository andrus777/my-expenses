package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface SubscriptionApi {
    @GET("subscriptions") suspend fun list(): Response<SubscriptionListResponse>
    @POST("subscriptions") suspend fun create(@Body body: SubscriptionRequest): Response<SubscriptionResponse>
    @PATCH("subscriptions/{id}") suspend fun update(@Path("id") id: String, @Body body: SubscriptionRequest): Response<SubscriptionResponse>
    @DELETE("subscriptions/{id}") suspend fun delete(@Path("id") id: String): Response<Unit>
    @GET("subscriptions/{id}/payments") suspend fun payments(@Path("id") id: String): Response<PaymentListResponse>
    @POST("subscriptions/{id}/payments") suspend fun pay(@Path("id") id: String, @Body body: PaymentRequest): Response<PaymentResponse>
}
