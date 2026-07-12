import React, { ReactNode, SelectHTMLAttributes, InputHTMLAttributes } from "react";

export function FormField({
  label,
  children,
  error,
}: {
  label: string;
  children: ReactNode;
  error?: string;
}) {
  return (
    <div className="block">
      <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-status-red font-medium">{error}</span>}
    </div>
  );
}

const base = "w-full rounded-lg border border-border bg-card px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/70 focus:border-primary/60 focus:outline-none focus:ring-2 focus:ring-primary/20 transition disabled:opacity-50 disabled:bg-muted";

export const TextInput = React.forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  (props, ref) => {
    return <input {...props} ref={ref} className={`${base} ${props.className ?? ""}`} />;
  }
);
TextInput.displayName = "TextInput";

export const Select = React.forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode }>(
  (props, ref) => {
    return (
      <select {...props} ref={ref} className={`${base} pr-8 ${props.className ?? ""}`}>
        {props.children}
      </select>
    );
  }
);
Select.displayName = "Select";
