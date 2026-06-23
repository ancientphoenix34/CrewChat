interface Props {
  title?: string
  message: string
  mode?: 'danger' | 'warning' | 'default'
  confirmLabel?: string
  onConfirm: () => void
  onCancel: () => void
}

const buttonStyles = {
  danger:  'bg-red-600 hover:bg-red-700 text-white',
  warning: 'bg-yellow-500 hover:bg-yellow-600 text-white',
  default: 'bg-purple-600 hover:bg-purple-700 text-white',
}

export default function ConfirmDialog({
  title,
  message,
  mode = 'default',
  confirmLabel = 'Confirm',
  onConfirm,
  onCancel,
}: Props) {
  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 mx-4"
        onClick={e => e.stopPropagation()}
      >
        {title && (
          <h2 className="text-base font-semibold text-gray-900 mb-1">{title}</h2>
        )}
        <p className="text-sm text-gray-500 mb-6">{message}</p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 rounded-lg py-2 text-sm font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${buttonStyles[mode]}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
