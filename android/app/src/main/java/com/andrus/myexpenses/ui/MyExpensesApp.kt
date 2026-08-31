package com.andrus.myexpenses.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Payments
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.andrus.myexpenses.domain.model.User
import com.andrus.myexpenses.domain.repository.AuthRepository
import com.andrus.myexpenses.presentation.AppViewModel
import com.andrus.myexpenses.presentation.AuthViewModel
import com.andrus.myexpenses.presentation.UiState

private const val LOGIN = "login"
private const val REGISTER = "register"
private const val MAIN = "main"

@Composable
fun MyExpensesApp(repository: AuthRepository) {
    val navController = rememberNavController()
    val appViewModel: AppViewModel = viewModel(factory = AppViewModel.Factory(repository))
    val authViewModel: AuthViewModel = viewModel(factory = AuthViewModel.Factory(repository))
    val appState by appViewModel.state.collectAsStateWithLifecycle()
    val authState by authViewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(appState) {
        when (appState) {
            is UiState.Content -> navController.navigate(MAIN) {
                popUpTo(navController.graph.findStartDestination().id) { inclusive = true }
                launchSingleTop = true
            }
            UiState.Empty -> navController.navigate(LOGIN) {
                popUpTo(navController.graph.findStartDestination().id) { inclusive = true }
                launchSingleTop = true
            }
            else -> Unit
        }
    }

    NavHost(navController = navController, startDestination = LOGIN) {
        composable(LOGIN) {
            LoginScreen(
                state = authState,
                onEmailChange = authViewModel::updateEmail,
                onPasswordChange = authViewModel::updatePassword,
                onSubmit = authViewModel::login,
                onRegister = { navController.navigate(REGISTER) },
            )
        }
        composable(REGISTER) {
            RegisterScreen(
                state = authState,
                onEmailChange = authViewModel::updateEmail,
                onPasswordChange = authViewModel::updatePassword,
                onConfirmationChange = authViewModel::updatePasswordConfirmation,
                onSubmit = authViewModel::register,
                onLogin = { navController.popBackStack() },
            )
        }
        composable(MAIN) {
            MainScreen(
                state = appState,
                onRetry = appViewModel::retry,
                onLogout = appViewModel::logout,
            )
        }
    }

    if (appState is UiState.Loading) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
    }
}

private data class MainDestination(
    val route: String,
    val label: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
)

private val destinations = listOf(
    MainDestination("home", "Главная", Icons.Default.Home),
    MainDestination("history", "История", Icons.Default.History),
    MainDestination("subscriptions", "Подписки", Icons.Default.Payments),
    MainDestination("statistics", "Статистика", Icons.Default.BarChart),
)

@Composable
private fun MainScreen(state: UiState<User>, onRetry: () -> Unit, onLogout: () -> Unit) {
    val navController = rememberNavController()
    val backStack by navController.currentBackStackEntryAsState()
    Scaffold(
        bottomBar = {
            NavigationBar {
                destinations.forEach { destination ->
                    NavigationBarItem(
                        selected = backStack?.destination?.route == destination.route,
                        onClick = {
                            navController.navigate(destination.route) {
                                popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(destination.icon, contentDescription = destination.label) },
                        label = { Text(destination.label) },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = destinations.first().route,
            modifier = Modifier.padding(padding),
        ) {
            composable("home") { StateContent(state, onRetry, onLogout) }
            composable("history") { EmptyPlaceholder("История расходов появится на следующем этапе") }
            composable("subscriptions") { EmptyPlaceholder("Подписки пока не добавлены") }
            composable("statistics") { EmptyPlaceholder("Статистика пока недоступна") }
        }
    }
}

@Composable
private fun StateContent(state: UiState<User>, onRetry: () -> Unit, onLogout: () -> Unit) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        when (state) {
            UiState.Loading -> CircularProgressIndicator()
            UiState.Empty -> EmptyPlaceholder("Данных пока нет")
            is UiState.Error -> Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(state.message)
                Button(onClick = onRetry) { Text("Повторить") }
            }
            is UiState.Content -> Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                Text("Вы вошли как ${state.value.email}")
                Button(onClick = onLogout) { Text("Выйти") }
            }
        }
    }
}

@Composable
private fun EmptyPlaceholder(message: String) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text(message) }
}
