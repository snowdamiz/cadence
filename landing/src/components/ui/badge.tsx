import { type HTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        salmon: 'bg-salmon/10 text-salmon border border-salmon/20',
        periwinkle: 'bg-periwinkle/10 text-periwinkle border border-periwinkle/20',
        outline: 'border border-white/10 text-white/60',
      },
    },
    defaultVariants: {
      variant: 'outline',
    },
  }
)

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />
}
