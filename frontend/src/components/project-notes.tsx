'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { updateProject } from '@/lib/api';
import { Check, Loader2 } from 'lucide-react';

interface ProjectNotesProps {
  projectId: string;
  initialNotes: string;
}

export function ProjectNotes({ projectId, initialNotes }: ProjectNotesProps) {
  const [notes, setNotes] = useState(initialNotes);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const save = useCallback(
    async (value: string) => {
      setSaving(true);
      try {
        await updateProject(projectId, { notes: value });
        setLastSaved(new Date());
      } catch {
        // Silently fail — user can retry
      } finally {
        setSaving(false);
      }
    },
    [projectId],
  );

  // Debounce auto-save on change
  useEffect(() => {
    if (notes === initialNotes && !lastSaved) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      save(notes);
    }, 2000);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [notes, save, initialNotes, lastSaved]);

  function handleBlur() {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    if (notes !== initialNotes || lastSaved) {
      save(notes);
    }
  }

  return (
    <div className="space-y-3">
      <Textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        onBlur={handleBlur}
        placeholder="Add project notes, meeting summaries, strategy ideas…"
        rows={12}
        className="font-mono text-sm"
      />
      <div className="flex items-center gap-2 text-xs text-[hsl(var(--muted-foreground))]">
        {saving ? (
          <>
            <Loader2 className="h-3 w-3 animate-spin" />
            Saving…
          </>
        ) : lastSaved ? (
          <>
            <Check className="h-3 w-3 text-emerald-500" />
            Last saved {lastSaved.toLocaleTimeString()}
          </>
        ) : (
          <span>Auto-saves after 2 seconds</span>
        )}
      </div>
    </div>
  );
}
