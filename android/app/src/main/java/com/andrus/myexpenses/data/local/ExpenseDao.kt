package com.andrus.myexpenses.data.local

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface ExpenseDao {
    @Query(
        """SELECT e.*, COALESCE(c.name, 'Без категории') AS categoryName
        FROM expenses e LEFT JOIN categories c
        ON c.ownerUserId = e.ownerUserId AND c.id = e.categoryId
        WHERE e.ownerUserId = :ownerId AND e.locallyDeleted = 0
        ORDER BY e.expenseDate DESC, e.createdAt DESC""",
    )
    fun observeVisible(ownerId: String): Flow<List<ExpenseWithCategory>>

    @Query("SELECT * FROM expenses WHERE localId = :localId AND ownerUserId = :ownerId")
    suspend fun find(localId: String, ownerId: String): ExpenseEntity?

    @Query("SELECT * FROM expenses WHERE ownerUserId = :ownerId AND pendingAction != 'NONE' ORDER BY createdAt")
    suspend fun pending(ownerId: String): List<ExpenseEntity>

    @Query("SELECT * FROM expenses WHERE ownerUserId = :ownerId AND syncStatus = 'SYNCED'")
    suspend fun synced(ownerId: String): List<ExpenseEntity>

    @Query("SELECT * FROM expenses WHERE ownerUserId = :ownerId AND clientOperationId = :operationId")
    suspend fun findByOperation(ownerId: String, operationId: String): ExpenseEntity?

    @Upsert
    suspend fun upsert(expense: ExpenseEntity)

    @Query("DELETE FROM expenses WHERE localId = :localId")
    suspend fun deletePermanently(localId: String)
}
