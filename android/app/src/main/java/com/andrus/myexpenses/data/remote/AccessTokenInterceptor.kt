package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.local.AuthLocalDataSource
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response

class AccessTokenInterceptor(
    private val authLocalDataSource: AuthLocalDataSource,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val accessToken = runBlocking { authLocalDataSource.currentTokens()?.accessToken }
        val request =
            if (accessToken == null || chain.request().header("Authorization") != null) {
                chain.request()
            } else {
                chain.request().newBuilder()
                    .header("Authorization", "Bearer $accessToken")
                    .build()
            }
        return chain.proceed(request)
    }
}
