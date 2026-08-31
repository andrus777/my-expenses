package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.local.AuthLocalDataSource
import com.andrus.myexpenses.data.local.UserLocalDataSource
import com.andrus.myexpenses.data.model.AuthResponse
import com.andrus.myexpenses.data.model.UserDto
import com.andrus.myexpenses.data.remote.AuthRemoteDataSource
import com.andrus.myexpenses.data.remote.UserRemoteDataSource
import com.andrus.myexpenses.domain.model.AuthTokens
import com.andrus.myexpenses.domain.model.User
import com.andrus.myexpenses.domain.repository.AuthRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class DefaultAuthRepository(
    private val authRemote: AuthRemoteDataSource,
    private val userRemote: UserRemoteDataSource,
    private val authLocal: AuthLocalDataSource,
    private val userLocal: UserLocalDataSource,
) : AuthRepository {
    override val isAuthenticated: Flow<Boolean> = authLocal.tokens.map { it != null }
    override val currentUser: Flow<User?> = userLocal.user

    override suspend fun register(email: String, password: String): User =
        persistAuth(authRemote.register(email, password))

    override suspend fun login(email: String, password: String): User =
        persistAuth(authRemote.login(email, password))

    override suspend fun refreshCurrentUser(): User {
        val user = userRemote.me().toDomain()
        userLocal.save(user)
        return user
    }

    override suspend fun logout() {
        val refreshToken = authLocal.currentTokens()?.refreshToken
        try {
            if (refreshToken != null) authRemote.logout(refreshToken)
        } finally {
            authLocal.clear()
            userLocal.clear()
        }
    }

    private suspend fun persistAuth(response: AuthResponse): User {
        val user = response.user.toDomain()
        userLocal.save(user)
        authLocal.saveTokens(
            AuthTokens(
                accessToken = response.tokens.access_token,
                refreshToken = response.tokens.refresh_token,
            ),
        )
        return user
    }

    private fun UserDto.toDomain() = User(id, email, created_at, updated_at)
}
