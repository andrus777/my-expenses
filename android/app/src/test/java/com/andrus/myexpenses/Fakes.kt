package com.andrus.myexpenses

import com.andrus.myexpenses.data.local.AuthLocalDataSource
import com.andrus.myexpenses.data.local.UserLocalDataSource
import com.andrus.myexpenses.data.model.AuthResponse
import com.andrus.myexpenses.data.model.TokenPairDto
import com.andrus.myexpenses.data.model.UserDto
import com.andrus.myexpenses.data.remote.AuthRemoteDataSource
import com.andrus.myexpenses.data.remote.UserRemoteDataSource
import com.andrus.myexpenses.domain.model.AuthTokens
import com.andrus.myexpenses.domain.model.User
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow

val testUserDto = UserDto("user-id", "user@example.com", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z")
val testUser = User(testUserDto.id, testUserDto.email, testUserDto.created_at, testUserDto.updated_at)

class FakeAuthRemoteDataSource : AuthRemoteDataSource {
    var loginResult = AuthResponse(testUserDto, TokenPairDto("access", "refresh"))
    var logoutFailure: Throwable? = null
    var logoutToken: String? = null

    override suspend fun register(email: String, password: String) = loginResult

    override suspend fun login(email: String, password: String) = loginResult

    override suspend fun logout(refreshToken: String) {
        logoutToken = refreshToken
        logoutFailure?.let { throw it }
    }
}

class FakeUserRemoteDataSource : UserRemoteDataSource {
    var result = testUserDto
    override suspend fun me(): UserDto = result
}

class FakeAuthLocalDataSource(initial: AuthTokens? = null) : AuthLocalDataSource {
    private val state = MutableStateFlow(initial)
    override val tokens: Flow<AuthTokens?> = state
    override suspend fun currentTokens(): AuthTokens? = state.value
    override suspend fun saveTokens(tokens: AuthTokens) { state.value = tokens }
    override suspend fun clear() { state.value = null }
}

class FakeUserLocalDataSource : UserLocalDataSource {
    private val state = MutableStateFlow<User?>(null)
    override val user: Flow<User?> = state
    override suspend fun save(user: User) { state.value = user }
    override suspend fun clear() { state.value = null }
}
