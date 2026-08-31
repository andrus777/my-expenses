package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.AuthResponse
import com.andrus.myexpenses.data.model.CredentialsRequest
import com.andrus.myexpenses.data.model.TokensResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST

interface AuthApi {
    @POST("auth/register")
    suspend fun register(@Body request: CredentialsRequest): Response<AuthResponse>

    @POST("auth/login")
    suspend fun login(@Body request: CredentialsRequest): Response<AuthResponse>

    @POST("auth/refresh")
    suspend fun refresh(@Header("Authorization") authorization: String): Response<TokensResponse>

    @POST("auth/logout")
    suspend fun logout(@Header("Authorization") authorization: String): Response<Unit>
}
