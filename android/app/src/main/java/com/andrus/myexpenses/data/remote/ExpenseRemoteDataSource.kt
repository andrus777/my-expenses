package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.CategoryDto
import com.andrus.myexpenses.data.model.ExpenseDto
import com.andrus.myexpenses.data.model.ExpensePatchRequest
import com.andrus.myexpenses.data.model.ExpenseRequest

interface ExpenseRemoteDataSource {
    suspend fun categories(): List<CategoryDto>
    suspend fun allExpenses(): List<ExpenseDto>
    suspend fun create(request: ExpenseRequest): ExpenseDto
    suspend fun update(id: String, request: ExpensePatchRequest): ExpenseDto
    suspend fun delete(id: String)
}

class RetrofitExpenseRemoteDataSource(
    private val api: ExpenseApi,
    private val responses: ResponseMapper,
) : ExpenseRemoteDataSource {
    override suspend fun categories() = responses.requireBody(api.categories()).items

    override suspend fun allExpenses(): List<ExpenseDto> {
        val items = mutableListOf<ExpenseDto>()
        var page = 1
        do {
            val response = responses.requireBody(api.expenses(page))
            items += response.items
            page++
        } while (page <= response.pagination.pages)
        return items
    }

    override suspend fun create(request: ExpenseRequest) = responses.requireBody(api.create(request)).expense

    override suspend fun update(id: String, request: ExpensePatchRequest) =
        responses.requireBody(api.update(id, request)).expense

    override suspend fun delete(id: String) {
        val response = api.delete(id)
        if (!response.isSuccessful && response.code() != 404) responses.requireBody(response)
    }
}
