'use client';

import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { downloadMarkdown } from '@/lib/utils';
import type { SavedPlay } from '@/lib/api';
import { Star, Trash2, Download, Edit3, Check, X } from 'lucide-react';

interface SavedPlaysListProps {
  plays: SavedPlay[];
  onRemove: (playId: string) => void;
  onUpdateNotes?: (playId: string, notes: string) => void;
}

export function SavedPlaysList({ plays, onRemove, onUpdateNotes }: SavedPlaysListProps) {
  if (plays.length === 0) {
    return (
      <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
        <Star className="h-10 w-10 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No saved plays yet. Star plays from iterations to save them here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {plays.map((play) => (
        <SavedPlayCard
          key={play.play_id}
          play={play}
          onRemove={() => onRemove(play.play_id)}
          onUpdateNotes={onUpdateNotes ? (notes) => onUpdateNotes(play.play_id, notes) : undefined}
        />
      ))}
    </div>
  );
}

function SavedPlayCard({
  play,
  onRemove,
  onUpdateNotes,
}: {
  play: SavedPlay;
  onRemove: () => void;
  onUpdateNotes?: (notes: string) => void;
}) {
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState(play.notes);

  function handleSaveNotes() {
    onUpdateNotes?.(notes);
    setEditingNotes(false);
  }

  function handleCancelNotes() {
    setNotes(play.notes);
    setEditingNotes(false);
  }

  function handleDownload() {
    const md = [
      `# ${play.play_data.title}`,
      '',
      `**Confidence:** ${Math.round(play.play_data.confidence_score * 100)}%`,
      '',
      `## Challenge`,
      play.play_data.challenge,
      '',
      `## Market Standard`,
      play.play_data.market_standard,
      '',
      `## Proposed Solution`,
      play.play_data.proposed_solution,
      '',
      `## Business Outcome`,
      play.play_data.business_outcome,
      '',
      play.play_data.technical_stack.length > 0
        ? `## Technical Stack\n${play.play_data.technical_stack.map((t) => `- ${t}`).join('\n')}`
        : '',
      '',
      play.play_data.citations.length > 0
        ? `## Citations\n${play.play_data.citations.map((c) => `- [${c.title}](${c.url}): ${c.snippet}`).join('\n')}`
        : '',
      notes ? `\n## Notes\n${notes}` : '',
    ]
      .filter(Boolean)
      .join('\n');
    downloadMarkdown(md, `${play.play_data.title.toLowerCase().replace(/\s+/g, '_')}.md`);
  }

  return (
    <Card className="border-l-4 border-l-amber-400">
      <CardContent className="p-5 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2 min-w-0">
            <Star className="h-4 w-4 text-amber-500 fill-amber-500 mt-0.5 flex-shrink-0" />
            <div className="min-w-0">
              <h4 className="font-semibold truncate">{play.play_data.title}</h4>
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5">
                From iteration {play.iteration_id.slice(0, 8)}…
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0">
            <Badge variant="outline">
              {Math.round(play.play_data.confidence_score * 100)}%
            </Badge>
          </div>
        </div>

        <p className="text-sm text-[hsl(var(--muted-foreground))]">{play.play_data.proposed_solution}</p>

        {/* Confidence bar */}
        <div className="h-1.5 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
          <div
            className="h-full rounded-full bg-amber-400 transition-all duration-500"
            style={{ width: `${play.play_data.confidence_score * 100}%` }}
          />
        </div>

        {/* Notes section */}
        {editingNotes ? (
          <div className="space-y-2">
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about this play…"
              rows={3}
              className="text-sm"
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSaveNotes}>
                <Check className="h-3 w-3" /> Save
              </Button>
              <Button size="sm" variant="outline" onClick={handleCancelNotes}>
                <X className="h-3 w-3" /> Cancel
              </Button>
            </div>
          </div>
        ) : (
          play.notes && (
            <p className="text-xs italic text-[hsl(var(--muted-foreground))] bg-[hsl(var(--muted))] rounded-lg px-3 py-2">
              {play.notes}
            </p>
          )
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-1">
          <Button size="sm" variant="ghost" onClick={() => setEditingNotes(true)}>
            <Edit3 className="h-3 w-3" /> Notes
          </Button>
          <Button size="sm" variant="ghost" onClick={handleDownload}>
            <Download className="h-3 w-3" /> Download
          </Button>
          <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-600" onClick={onRemove}>
            <Trash2 className="h-3 w-3" /> Remove
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
