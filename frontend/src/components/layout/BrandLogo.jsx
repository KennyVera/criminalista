import { Shield } from 'lucide-react'

export default function BrandLogo({ className = 'h-10 w-10' }) {
  return (
    <div
      className={`${className} relative flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] shadow-lg shadow-indigo-500/25`}
    >
      <Shield className="h-[55%] w-[55%] text-white" strokeWidth={2} aria-hidden />
    </div>
  )
}
