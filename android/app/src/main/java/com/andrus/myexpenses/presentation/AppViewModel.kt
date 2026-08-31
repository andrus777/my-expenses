package com.andrus.myexpenses.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.andrus.myexpenses.domain.model.User
import com.andrus.myexpenses.domain.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class AppViewModel(private val repository: AuthRepository) : ViewModel() {
    private val mutableState = MutableStateFlow<UiState<User>>(UiState.Loading)
    val state: StateFlow<UiState<User>> = mutableState.asStateFlow()

    init {
        viewModelScope.launch {
            repository.isAuthenticated.collect { authenticated ->
                if (!authenticated) {
                    mutableState.value = UiState.Empty
                } else {
                    mutableState.value = UiState.Loading
                    runCatching { repository.refreshCurrentUser() }
                        .onSuccess { mutableState.value = UiState.Content(it) }
                        .onFailure {
                            mutableState.value = UiState.Error(it.message ?: "Не удалось загрузить профиль")
                        }
                }
            }
        }
    }

    fun retry() {
        viewModelScope.launch {
            mutableState.value = UiState.Loading
            runCatching { repository.refreshCurrentUser() }
                .onSuccess { mutableState.value = UiState.Content(it) }
                .onFailure { mutableState.value = UiState.Error(it.message ?: "Не удалось загрузить профиль") }
        }
    }

    fun logout() = viewModelScope.launch { runCatching { repository.logout() } }

    class Factory(private val repository: AuthRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = AppViewModel(repository) as T
    }
}
