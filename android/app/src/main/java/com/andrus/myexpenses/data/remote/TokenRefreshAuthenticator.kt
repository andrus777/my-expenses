package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.local.AuthLocalDataSource
import com.andrus.myexpenses.domain.model.AuthTokens
import kotlinx.coroutines.runBlocking
import okhttp3.Authenticator
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route

class TokenRefreshAuthenticator(
    private val authLocalDataSource: AuthLocalDataSource,
    private val refreshApi: AuthApi,
) : Authenticator {
    private val refreshLock = Any()

    override fun authenticate(route: Route?, response: Response): Request? {
        if (responseCount(response) >= MAX_ATTEMPTS || response.request.header(RETRY_HEADER) != null) {
            return null
        }
        return synchronized(refreshLock) {
            runBlocking { retryWithFreshToken(response) }
        }
    }

    private suspend fun retryWithFreshToken(response: Response): Request? {
        val tokens = authLocalDataSource.currentTokens() ?: return null
        val requestAccessToken = response.request.header("Authorization")?.removePrefix("Bearer ")
        if (requestAccessToken != null && requestAccessToken != tokens.accessToken) {
            return response.request.withAccessToken(tokens.accessToken)
        }

        val refreshed = runCatching {
            refreshApi.refresh("Bearer ${tokens.refreshToken}")
        }.getOrNull()
        val pair = refreshed?.takeIf { it.isSuccessful }?.body()?.tokens
        if (pair == null) {
            authLocalDataSource.clear()
            return null
        }
        val newTokens = AuthTokens(pair.access_token, pair.refresh_token)
        authLocalDataSource.saveTokens(newTokens)
        return response.request.withAccessToken(newTokens.accessToken)
    }

    private fun Request.withAccessToken(accessToken: String): Request =
        newBuilder()
            .header("Authorization", "Bearer $accessToken")
            .header(RETRY_HEADER, "1")
            .build()

    private fun responseCount(response: Response): Int {
        var count = 1
        var previous = response.priorResponse
        while (previous != null) {
            count++
            previous = previous.priorResponse
        }
        return count
    }

    private companion object {
        const val RETRY_HEADER = "X-Auth-Retry"
        const val MAX_ATTEMPTS = 2
    }
}
