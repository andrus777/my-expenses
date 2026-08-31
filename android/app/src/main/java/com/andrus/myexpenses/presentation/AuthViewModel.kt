package com.andrus.myexpenses.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.andrus.myexpenses.domain.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class AuthUiState(
    val email: String = "",
    val password: String = "",
    val passwordConfirmation: String = "",
    val result: UiState<Unit> = UiState.Empty,
)

class AuthViewModel(private val repository: AuthRepository) : ViewModel() {
    private val mutableState = MutableStateFlow(AuthUiState())
    val state: StateFlow<AuthUiState> = mutableState.asStateFlow()

    fun updateEmail(value: String) = mutableState.update { it.copy(email = value) }

    fun updatePassword(value: String) = mutableState.update { it.copy(password = value) }

    fun updatePasswordConfirmation(value: String) =
        mutableState.update { it.copy(passwordConfirmation = value) }

    fun login() = submit { email, password -> repository.login(email, password) }

    fun register() {
        val snapshot = state.value
        if (snapshot.password != snapshot.passwordConfirmation) {
            mutableState.update { it.copy(result = UiState.Error("Пароли не совпадают")) }
            return
        }
        submit { email, password -> repository.register(email, password) }
    }

    private fun submit(action: suspend (String, String) -> Unit) {
        val snapshot = state.value
        when {
            snapshot.email.isBlank() -> setError("Введите email")
            snapshot.password.length < 8 -> setError("Пароль должен содержать не менее 8 символов")
            snapshot.result is UiState.Loading -> return
            else -> viewModelScope.launch {
                mutableState.update { it.copy(result = UiState.Loading) }
                runCatching { action(snapshot.email.trim(), snapshot.password) }
                    .onSuccess { mutableState.update { state -> state.copy(result = UiState.Content(Unit)) } }
                    .onFailure { error -> setError(error.message ?: "Не удалось выполнить запрос") }
            }
        }
    }

    private fun setError(message: String) =
        mutableState.update { it.copy(result = UiState.Error(message)) }

    class Factory(private val repository: AuthRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = AuthViewModel(repository) as T
    }
}
