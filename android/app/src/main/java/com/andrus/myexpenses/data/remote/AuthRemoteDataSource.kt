package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.AuthResponse
import com.andrus.myexpenses.data.model.CredentialsRequest

interface AuthRemoteDataSource {
    suspend fun register(email: String, password: String): AuthResponse

    suspend fun login(email: String, password: String): AuthResponse

    suspend fun logout(refreshToken: String)
}

class RetrofitAuthRemoteDataSource(
    private val api: AuthApi,
    private val responses: ResponseMapper,
) : AuthRemoteDataSource {
    override suspend fun register(email: String, password: String): AuthResponse =
        responses.requireBody(api.register(CredentialsRequest(email, password)))

    override suspend fun login(email: String, password: String): AuthResponse =
        responses.requireBody(api.login(CredentialsRequest(email, password)))

    override suspend fun logout(refreshToken: String) {
        val response = api.logout("Bearer $refreshToken")
        if (!response.isSuccessful && response.code() != 401) {
            responses.requireBody(response)
        }
    }
}
