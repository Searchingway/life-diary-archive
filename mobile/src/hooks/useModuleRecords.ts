import { useCallback, useEffect, useState } from "react";

import { useRepository } from "@/db/RepositoryContext";
import type { ArchiveRecord, ModuleKey } from "@/domain/models";

export function useModuleRecords(module: ModuleKey) {
  const repository = useRepository();
  const [records, setRecords] = useState<ArchiveRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(
    async (query = "") => {
      setLoading(true);
      try {
        setRecords(await repository.list(module, query));
      } finally {
        setLoading(false);
      }
    },
    [module, repository],
  );

  useEffect(() => {
    const timer = setTimeout(() => void refresh(), 0);
    return () => clearTimeout(timer);
  }, [refresh]);

  return { repository, records, loading, refresh };
}
