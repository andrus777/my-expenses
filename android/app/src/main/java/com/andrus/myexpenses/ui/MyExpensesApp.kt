package com.andrus.myexpenses.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.*
import com.andrus.myexpenses.domain.model.Category
import com.andrus.myexpenses.domain.model.Expense
import com.andrus.myexpenses.domain.model.SyncStatus
import com.andrus.myexpenses.domain.repository.AuthRepository
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import com.andrus.myexpenses.domain.repository.SubscriptionRepository
import com.andrus.myexpenses.presentation.*
import java.math.BigDecimal
import java.time.LocalDate

private const val LOGIN = "login"
private const val REGISTER = "register"
private const val MAIN = "main"

@Composable
fun MyExpensesApp(
    authRepository: AuthRepository,
    expenseRepository: ExpenseRepository,
    subscriptionRepository: SubscriptionRepository,
) {
    val navController = rememberNavController()
    val appViewModel: AppViewModel = viewModel(factory = AppViewModel.Factory(authRepository))
    val authViewModel: AuthViewModel = viewModel(factory = AuthViewModel.Factory(authRepository))
    val expenseViewModel: ExpenseViewModel = viewModel(factory = ExpenseViewModel.Factory(expenseRepository))
    val subscriptionViewModel: SubscriptionViewModel = viewModel(
        factory = SubscriptionViewModel.Factory(subscriptionRepository, expenseRepository),
    )
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
        if (appState is UiState.Content) {
            expenseViewModel.refresh()
            subscriptionViewModel.refresh()
        }
    }
    NavHost(navController, startDestination = LOGIN) {
        composable(LOGIN) {
            LoginScreen(authState, authViewModel::updateEmail, authViewModel::updatePassword, authViewModel::login) {
                navController.navigate(REGISTER)
            }
        }
        composable(REGISTER) {
            RegisterScreen(
                authState,
                authViewModel::updateEmail,
                authViewModel::updatePassword,
                authViewModel::updatePasswordConfirmation,
                authViewModel::register,
            ) { navController.popBackStack() }
        }
        composable(MAIN) { MainScreen(expenseViewModel, subscriptionViewModel, appViewModel::logout) }
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
private fun MainScreen(
    viewModel: ExpenseViewModel,
    subscriptionViewModel: SubscriptionViewModel,
    onLogout: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val navController = rememberNavController()
    val backStack by navController.currentBackStackEntryAsState()
    val route = backStack?.destination?.route
    Scaffold(
        bottomBar = {
            if (route in destinations.map { it.route }) NavigationBar {
                destinations.forEach { destination ->
                    NavigationBarItem(
                        selected = route == destination.route,
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
        floatingActionButton = {
            if (route == "home" || route == "history") {
                ExtendedFloatingActionButton(
                    onClick = { navController.navigate("expense/add") },
                    icon = { Icon(Icons.Default.Add, contentDescription = null) },
                    text = { Text("Добавить") },
                )
            }
        },
    ) { padding ->
        NavHost(navController, "home", Modifier.padding(padding)) {
            composable("home") { HomeScreen(state, onLogout) { navController.navigate("expense/edit/$it") } }
            composable("history") { HistoryScreen(state, viewModel::retry) { navController.navigate("expense/edit/$it") } }
            composable("expense/add") {
                ExpenseForm(null, state.categories, viewModel::save, onDone = { navController.popBackStack() })
            }
            composable("expense/edit/{localId}") { entry ->
                val expense = state.expenses.firstOrNull { it.localId == entry.arguments?.getString("localId") }
                if (expense == null) {
                    Placeholder("Расход не найден")
                } else {
                    ExpenseForm(expense, state.categories, viewModel::save, viewModel::delete) {
                        navController.popBackStack()
                    }
                }
            }
            composable("subscriptions") { SubscriptionScreen(subscriptionViewModel) }
            composable("statistics") { Placeholder("Статистика пока недоступна") }
        }
    }
}

@Composable
private fun HomeScreen(state: ExpensesUiState, onLogout: () -> Unit, onEdit: (String) -> Unit) {
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Мои расходы", style = MaterialTheme.typography.headlineMedium)
        Text("Всего: ${state.expenses.sumOf { it.amountMinor }.money()} RUB")
        SyncBanner(state)
        Spacer(Modifier.height(16.dp))
        Text("Последние операции", style = MaterialTheme.typography.titleMedium)
        Box(Modifier.weight(1f)) { ExpenseList(state.expenses.take(5), onEdit) }
        TextButton(onClick = onLogout) { Text("Выйти") }
    }
}

@Composable
private fun HistoryScreen(state: ExpensesUiState, onRetry: (String) -> Unit, onEdit: (String) -> Unit) {
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("История", style = MaterialTheme.typography.headlineMedium)
        SyncBanner(state)
        ExpenseList(state.expenses, onEdit, onRetry)
    }
}

@Composable
private fun SyncBanner(state: ExpensesUiState) {
    when {
        state.errorCount > 0 -> Text(
            "Не удалось синхронизировать ${state.errorCount} операций. Можно повторить вручную.",
            color = MaterialTheme.colorScheme.error,
        )
        state.pendingCount > 0 -> Text("Сохранено на устройстве. Отправим при появлении сети.")
    }
}

@Composable
private fun ExpenseList(expenses: List<Expense>, onEdit: (String) -> Unit, onRetry: (String) -> Unit = {}) {
    if (expenses.isEmpty()) {
        Placeholder("Расходов пока нет")
        return
    }
    LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(expenses, key = { it.localId }) { expense ->
            Card(Modifier.fillMaxWidth().clickable { onEdit(expense.localId) }) {
                Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    Column {
                        Text(expense.categoryName)
                        Text(expense.expenseDate, style = MaterialTheme.typography.bodySmall)
                        when (expense.syncStatus) {
                            SyncStatus.PENDING_SYNC -> Text("Ожидает синхронизации")
                            SyncStatus.SYNC_ERROR -> TextButton(onClick = { onRetry(expense.localId) }) {
                                Text("Ошибка — повторить")
                            }
                            SyncStatus.SYNCED -> Unit
                        }
                    }
                    Text("${expense.amountMinor.money()} ${expense.currency}")
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ExpenseForm(
    expense: Expense?,
    categories: List<Category>,
    onSave: (String?, String, String, String) -> String?,
    onDelete: (String) -> Unit = {},
    onDone: () -> Unit,
) {
    var amount by remember(expense?.localId) { mutableStateOf(expense?.amountMinor?.money().orEmpty()) }
    var categoryId by remember(expense?.localId) { mutableStateOf(expense?.categoryId.orEmpty()) }
    var menuExpanded by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showDelete by remember { mutableStateOf(false) }
    Scaffold(topBar = { TopAppBar(title = { Text(if (expense == null) "Добавить расход" else "Редактировать расход") }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp)) {
            OutlinedTextField(
                value = amount,
                onValueChange = { amount = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Сумма") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))
            Box {
                Button(onClick = { menuExpanded = true }, enabled = categories.isNotEmpty()) {
                    Text(categories.firstOrNull { it.id == categoryId }?.name ?: "Выберите категорию")
                }
                DropdownMenu(expanded = menuExpanded, onDismissRequest = { menuExpanded = false }) {
                    categories.forEach { category ->
                        DropdownMenuItem(
                            text = { Text(category.name) },
                            onClick = { categoryId = category.id; menuExpanded = false },
                        )
                    }
                }
            }
            if (categories.isEmpty()) Text("Категории не загружены. Подключитесь к сети и откройте экран снова.")
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Spacer(Modifier.height(20.dp))
            Button(
                onClick = {
                    error = onSave(expense?.localId, amount, categoryId, expense?.expenseDate ?: LocalDate.now().toString())
                    if (error == null) onDone()
                },
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Сохранить") }
            if (expense != null) TextButton(onClick = { showDelete = true }) { Text("Удалить расход") }
        }
    }
    if (showDelete && expense != null) {
        AlertDialog(
            onDismissRequest = { showDelete = false },
            title = { Text("Удалить расход?") },
            text = { Text("Расход исчезнет сразу и будет удалён на сервере при синхронизации.") },
            confirmButton = { TextButton(onClick = { onDelete(expense.localId); onDone() }) { Text("Удалить") } },
            dismissButton = { TextButton(onClick = { showDelete = false }) { Text("Отмена") } },
        )
    }
}

@Composable
private fun Placeholder(message: String) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text(message) }
}

private fun Long.money() = BigDecimal.valueOf(this, 2).toPlainString()
