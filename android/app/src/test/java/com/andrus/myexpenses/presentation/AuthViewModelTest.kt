package com.andrus.myexpenses.presentation

import com.andrus.myexpenses.MainDispatcherRule
import com.andrus.myexpenses.domain.model.User
import com.andrus.myexpenses.domain.repository.AuthRepository
import com.andrus.myexpenses.testUser
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class AuthViewModelTest {
    @get:Rule val dispatcherRule = MainDispatcherRule()

    @Test
    fun `login delegates trimmed email and exposes content`() = runTest {
        val repository = FakeRepository()
        val viewModel = AuthViewModel(repository)
        viewModel.updateEmail(" user@example.com ")
        viewModel.updatePassword("password123")

        viewModel.login()

        assertEquals("user@example.com", repository.loginEmail)
        assertTrue(viewModel.state.value.result is UiState.Content)
    }

    @Test
    fun `registration rejects mismatched passwords`() {
        val repository = FakeRepository()
        val viewModel = AuthViewModel(repository)
        viewModel.updateEmail("user@example.com")
        viewModel.updatePassword("password123")
        viewModel.updatePasswordConfirmation("different")

        viewModel.register()

        assertEquals("Пароли не совпадают", (viewModel.state.value.result as UiState.Error).message)
        assertEquals(0, repository.registerCalls)
    }
}

private class FakeRepository : AuthRepository {
    override val isAuthenticated: Flow<Boolean> = MutableStateFlow(false)
    override val currentUser: Flow<User?> = MutableStateFlow(null)
    var loginEmail: String? = null
    var registerCalls = 0

    override suspend fun register(email: String, password: String): User {
        registerCalls++
        return testUser
    }

    override suspend fun login(email: String, password: String): User {
        loginEmail = email
        return testUser
    }

    override suspend fun refreshCurrentUser(): User = testUser
    override suspend fun logout() = Unit
}
