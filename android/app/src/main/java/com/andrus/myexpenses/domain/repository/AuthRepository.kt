package com.andrus.myexpenses.domain.repository

import com.andrus.myexpenses.domain.model.User
import kotlinx.coroutines.flow.Flow

interface AuthRepository {
    val isAuthenticated: Flow<Boolean>
    val currentUser: Flow<User?>

    suspend fun register(email: String, password: String): User

    suspend fun login(email: String, password: String): User

    suspend fun refreshCurrentUser(): User

    suspend fun logout()
}
