package com.andrus.myexpenses.data.local

import com.andrus.myexpenses.domain.model.AuthTokens
import kotlinx.coroutines.flow.Flow

interface AuthLocalDataSource {
    val tokens: Flow<AuthTokens?>

    suspend fun currentTokens(): AuthTokens?

    suspend fun saveTokens(tokens: AuthTokens)

    suspend fun clear()
}
