package com.andrus.myexpenses.data.repository

import app.cash.turbine.test
import com.andrus.myexpenses.FakeAuthLocalDataSource
import com.andrus.myexpenses.FakeAuthRemoteDataSource
import com.andrus.myexpenses.FakeUserLocalDataSource
import com.andrus.myexpenses.FakeUserRemoteDataSource
import com.andrus.myexpenses.domain.model.AuthTokens
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test

class DefaultAuthRepositoryTest {
    @Test
    fun `login stores tokens and user`() = runTest {
        val authLocal = FakeAuthLocalDataSource()
        val userLocal = FakeUserLocalDataSource()
        val repository = repository(authLocal, userLocal)

        val user = repository.login("user@example.com", "password123")

        assertEquals("user@example.com", user.email)
        assertEquals(AuthTokens("access", "refresh"), authLocal.currentTokens())
        userLocal.user.test { assertEquals(user, awaitItem()); cancelAndIgnoreRemainingEvents() }
    }

    @Test
    fun `logout clears local auth even when server call fails`() = runTest {
        val authLocal = FakeAuthLocalDataSource(AuthTokens("access", "refresh"))
        val userLocal = FakeUserLocalDataSource()
        val remote = FakeAuthRemoteDataSource().apply { logoutFailure = IllegalStateException("offline") }
        val repository = repository(authLocal, userLocal, remote)

        runCatching { repository.logout() }

        assertNull(authLocal.currentTokens())
        repository.isAuthenticated.test { assertFalse(awaitItem()); cancelAndIgnoreRemainingEvents() }
        assertEquals("refresh", remote.logoutToken)
    }

    private fun repository(
        authLocal: FakeAuthLocalDataSource,
        userLocal: FakeUserLocalDataSource,
        remote: FakeAuthRemoteDataSource = FakeAuthRemoteDataSource(),
    ) = DefaultAuthRepository(remote, FakeUserRemoteDataSource(), authLocal, userLocal)
}
