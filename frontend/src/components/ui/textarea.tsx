import { cn } from '@/lib/utils';
import { forwardRef } from 'react';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      className={cn(
        'flex min-h-[80px] w-full rounded-lg border bg-transparent px-3 py-2 text-sm transition-colors',
        'placeholder:text-[hsl(var(--muted-foreground))]',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pellera-500',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
Textarea.displayName = 'Textarea';
