export default function Logo({ size = 36 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Main chat bubble */}
      <rect x="2" y="2" width="24" height="18" rx="5" fill="#7c3aed" />
      {/* Tail of main bubble */}
      <path d="M8 20 L6 26 L14 20Z" fill="#7c3aed" />
      {/* Second chat bubble (offset) */}
      <rect x="12" y="14" width="22" height="16" rx="5" fill="#a855f7" />
      {/* Tail of second bubble */}
      <path d="M28 30 L30 36 L22 30Z" fill="#a855f7" />
      {/* Dots on main bubble */}
      <circle cx="9"  cy="11" r="2" fill="white" />
      <circle cx="15" cy="11" r="2" fill="white" />
      <circle cx="21" cy="11" r="2" fill="white" />
    </svg>
  )
}
