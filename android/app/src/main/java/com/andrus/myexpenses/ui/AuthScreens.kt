package com.andrus.myexpenses.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.andrus.myexpenses.presentation.AuthUiState
import com.andrus.myexpenses.presentation.UiState

@Composable
fun LoginScreen(
    state: AuthUiState,
    onEmailChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onRegister: () -> Unit,
) {
    AuthForm(
        title = "Вход",
        action = "Войти",
        alternate = "Создать аккаунт",
        state = state,
        onEmailChange = onEmailChange,
        onPasswordChange = onPasswordChange,
        onSubmit = onSubmit,
        onAlternate = onRegister,
    )
}

@Composable
fun RegisterScreen(
    state: AuthUiState,
    onEmailChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onConfirmationChange: (String) -> Unit,
    onSubmit: () -> Unit,
    onLogin: () -> Unit,
) {
    AuthForm(
        title = "Регистрация",
        action = "Зарегистрироваться",
        alternate = "Уже есть аккаунт",
        state = state,
        showConfirmation = true,
        onEmailChange = onEmailChange,
        onPasswordChange = onPasswordChange,
        onConfirmationChange = onConfirmationChange,
        onSubmit = onSubmit,
        onAlternate = onLogin,
    )
}

@Composable
private fun AuthForm(
    title: String,
    action: String,
    alternate: String,
    state: AuthUiState,
    showConfirmation: Boolean = false,
    onEmailChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onConfirmationChange: (String) -> Unit = {},
    onSubmit: () -> Unit,
    onAlternate: () -> Unit,
) {
    val loading = state.result is UiState.Loading
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(title, style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(24.dp))
        OutlinedTextField(
            value = state.email,
            onValueChange = onEmailChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Email") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            singleLine = true,
            enabled = !loading,
        )
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = state.password,
            onValueChange = onPasswordChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Пароль") },
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            singleLine = true,
            enabled = !loading,
        )
        if (showConfirmation) {
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = state.passwordConfirmation,
                onValueChange = onConfirmationChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Повторите пароль") },
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                singleLine = true,
                enabled = !loading,
            )
        }
        if (state.result is UiState.Error) {
            Spacer(Modifier.height(12.dp))
            Text(state.result.message, color = MaterialTheme.colorScheme.error)
        }
        Spacer(Modifier.height(20.dp))
        Button(onClick = onSubmit, enabled = !loading, modifier = Modifier.fillMaxWidth()) {
            if (loading) CircularProgressIndicator(modifier = Modifier.height(20.dp)) else Text(action)
        }
        TextButton(onClick = onAlternate, enabled = !loading) { Text(alternate) }
    }
}
