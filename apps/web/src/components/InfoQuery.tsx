import React, { useMemo } from 'react'
import {
  FiChevronLeft,
  FiChevronRight,
  FiChevronsLeft,
  FiChevronsRight,
  FiMoreHorizontal,
} from 'react-icons/fi'
import './InfoQuery.css'

export type TableAlign = 'left' | 'center' | 'right'

export interface TableColumn<T> {
  key: string
  header: string
  align?: TableAlign
  bold?: boolean
  render?: (row: T, index: number) => React.ReactNode
}

export interface TablePaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export interface InfoQueryTableProps<T> {
  columns: TableColumn<T>[]
  data: T[]
  rowKey: (row: T, index: number) => string | number
  emptyMessage?: string
  pagination?: TablePaginationProps
}

function getPageNumbers(current: number, total: number): (number | '...')[] {
  const MAX_SLOTS = 10
  if (total <= MAX_SLOTS) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  if (current <= 6) {
    return [1, 2, 3, 4, 5, 6, 7, 8, '...', total]
  }

  if (current >= total - 5) {
    return [
      1,
      '...',
      total - 7,
      total - 6,
      total - 5,
      total - 4,
      total - 3,
      total - 2,
      total - 1,
      total,
    ]
  }

  const startMid = current - 2
  return [
    1,
    '...',
    startMid,
    startMid + 1,
    startMid + 2,
    startMid + 3,
    startMid + 4,
    startMid + 5,
    '...',
    total,
  ]
}

/**
 * 정보 조회 페이지 공통 데이터 테이블 컴포넌트
 */
export function InfoQueryTable<T>({
  columns,
  data,
  rowKey,
  emptyMessage = '데이터가 없습니다.',
  pagination,
}: InfoQueryTableProps<T>) {
  const hasPagination = Boolean(pagination && pagination.totalPages > 1)
  const validCurrentPage = pagination
    ? Math.min(Math.max(pagination.currentPage, 1), pagination.totalPages)
    : 1

  const pageNumbers = useMemo(() => {
    if (!pagination || pagination.totalPages <= 1) return []
    return getPageNumbers(validCurrentPage, pagination.totalPages)
  }, [pagination, validCurrentPage])

  return (
    <div className="info-query-table-container">
      <div className="info-query-table__wrapper">
        <table className="info-query-table">
          <thead className="info-query-table__head">
            <tr>
              {columns.map((col) => {
                const alignClass =
                  col.align === 'center'
                    ? 'info-query-table__header--center'
                    : col.align === 'right'
                    ? 'info-query-table__header--right'
                    : ''
                return (
                  <th key={col.key} className={`info-query-table__header ${alignClass}`.trim()}>
                    {col.header}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody className="info-query-table__body">
            {data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="info-query-table__empty">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, rowIndex) => (
                <tr key={rowKey(row, rowIndex)} className="info-query-table__row">
                  {columns.map((col) => {
                    const alignClass =
                      col.align === 'center'
                        ? 'info-query-table__cell--center'
                        : col.align === 'right'
                        ? 'info-query-table__cell--right'
                        : ''
                    const boldClass = col.bold ? 'info-query-table__cell--bold' : ''
                    return (
                      <td
                        key={col.key}
                        className={`info-query-table__cell ${alignClass} ${boldClass}`.trim()}
                      >
                        {col.render
                          ? col.render(row, rowIndex)
                          : String((row as Record<string, any>)[col.key] ?? '-')}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls (totalPages > 1 일 때만 자동 노출) */}
      {hasPagination && pagination && (
        <div className="info-query-table__pagination">
          <button
            type="button"
            className="info-query-table__pagination-button"
            title="10페이지 이전"
            disabled={validCurrentPage <= 1}
            onClick={() => pagination.onPageChange(validCurrentPage - 10)}
          >
            <FiChevronsLeft size={16} />
          </button>

          <button
            type="button"
            className="info-query-table__pagination-button"
            title="이전 페이지"
            disabled={validCurrentPage <= 1}
            onClick={() => pagination.onPageChange(validCurrentPage - 1)}
          >
            <FiChevronLeft size={16} />
          </button>

          {pageNumbers.map((item, idx) => {
            if (item === '...') {
              return (
                <span
                  key={`ellipsis-${idx}`}
                  className="info-query-table__pagination-ellipsis"
                >
                  <FiMoreHorizontal size={14} />
                </span>
              )
            }
            return (
              <button
                key={item}
                type="button"
                className={`info-query-table__pagination-button ${
                  item === validCurrentPage
                    ? 'info-query-table__pagination-button--active'
                    : ''
                }`}
                onClick={() => pagination.onPageChange(item)}
              >
                {item}
              </button>
            )
          })}

          <button
            type="button"
            className="info-query-table__pagination-button"
            title="다음 페이지"
            disabled={validCurrentPage >= pagination.totalPages}
            onClick={() => pagination.onPageChange(validCurrentPage + 1)}
          >
            <FiChevronRight size={16} />
          </button>

          <button
            type="button"
            className="info-query-table__pagination-button"
            title="10페이지 다음"
            disabled={validCurrentPage >= pagination.totalPages}
            onClick={() => pagination.onPageChange(validCurrentPage + 10)}
          >
            <FiChevronsRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
