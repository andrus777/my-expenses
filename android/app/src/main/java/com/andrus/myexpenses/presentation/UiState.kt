package com.andrus.myexpenses.presentation

sealed interface UiState<out T> {
    data object Loading : UiState<Nothing>

    data class Content<T>(val value: T) : UiState<T>

    data object Empty : UiState<Nothing>

    data class Error(val message: String) : UiState<Nothing>
}
