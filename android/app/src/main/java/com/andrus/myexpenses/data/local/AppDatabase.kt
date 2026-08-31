package com.andrus.myexpenses.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [UserEntity::class, ExpenseEntity::class, CategoryEntity::class],
    version = 2,
    exportSchema = true,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao

    abstract fun expenseDao(): ExpenseDao

    abstract fun categoryDao(): CategoryDao

    companion object {
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL(
                    """CREATE TABLE IF NOT EXISTS `categories` (
                        `ownerUserId` TEXT NOT NULL, `id` TEXT NOT NULL, `name` TEXT NOT NULL,
                        `isSystem` INTEGER NOT NULL,
                        PRIMARY KEY(`ownerUserId`, `id`))""",
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS `index_categories_ownerUserId` ON `categories` (`ownerUserId`)")
                db.execSQL(
                    """CREATE TABLE IF NOT EXISTS `expenses` (
                        `localId` TEXT NOT NULL, `ownerUserId` TEXT NOT NULL, `serverId` TEXT,
                        `categoryId` TEXT NOT NULL, `amountMinor` INTEGER NOT NULL,
                        `currency` TEXT NOT NULL, `expenseDate` TEXT NOT NULL, `merchant` TEXT,
                        `description` TEXT, `comment` TEXT, `source` TEXT NOT NULL,
                        `clientOperationId` TEXT NOT NULL, `createdAt` TEXT NOT NULL,
                        `updatedAt` TEXT NOT NULL, `syncStatus` TEXT NOT NULL,
                        `pendingAction` TEXT NOT NULL, `locallyDeleted` INTEGER NOT NULL,
                        PRIMARY KEY(`localId`))""",
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS `index_expenses_ownerUserId_expenseDate` ON `expenses` (`ownerUserId`, `expenseDate`)")
                db.execSQL("CREATE INDEX IF NOT EXISTS `index_expenses_ownerUserId_categoryId` ON `expenses` (`ownerUserId`, `categoryId`)")
                db.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_expenses_ownerUserId_clientOperationId` ON `expenses` (`ownerUserId`, `clientOperationId`)")
                db.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_expenses_serverId` ON `expenses` (`serverId`)")
            }
        }
    }
}
