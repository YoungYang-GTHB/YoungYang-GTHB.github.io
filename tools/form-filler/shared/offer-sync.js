(function (root, factory) {
  const api = factory();

  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }

  root.OfferJobSync = api;
})(
  typeof globalThis !== "undefined" ? globalThis : this,
  function () {
    "use strict";

    const OFFER_ORIGIN = "https://offerqingbaoju.cn";
    const IMPORT_DIRECTORY = ["skills", "job-hunter", "imports"];

    function isOfferSiteUrl(value) {
      try {
        return new URL(String(value || "")).origin === OFFER_ORIGIN;
      } catch (_) {
        return false;
      }
    }

    function formatDate(value) {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "1970-01-01";
      return date.toISOString().slice(0, 10);
    }

    function buildImportFileName({ observedAt, navigationId }) {
      const date = formatDate(observedAt);
      const navId = Number(navigationId) || 0;
      return `${date}_offer-nav${navId}_raw.jsonl`;
    }

    function createExportRecords(records, metadata) {
      const safeRecords = Array.isArray(records) ? records : [];
      const observedAt = metadata?.observedAt || new Date().toISOString();

      return safeRecords
        .filter((record) => record && typeof record === "object" && !Array.isArray(record))
        .map((record) => ({
          ...record,
          _platform: "offer情报局",
          _source_type: "browser_visible",
          _source: metadata?.navigationName || "",
          _navigation_id: Number(metadata?.navigationId) || null,
          _observed_at: observedAt,
        }));
    }

    function toJsonl(records) {
      const lines = (Array.isArray(records) ? records : []).map((record) =>
        JSON.stringify(record)
      );
      return lines.length ? `${lines.join("\n")}\n` : "";
    }

    async function ensureNestedDirectory(rootHandle, segments) {
      if (!rootHandle || typeof rootHandle.getDirectoryHandle !== "function") {
        throw new Error("未配置项目目录");
      }

      let current = rootHandle;
      for (const segment of segments) {
        current = await current.getDirectoryHandle(segment, { create: true });
      }
      return current;
    }

    async function writeImportFile(rootHandle, { records, observedAt, navigationId }) {
      const directory = await ensureNestedDirectory(rootHandle, IMPORT_DIRECTORY);
      const fileName = buildImportFileName({ observedAt, navigationId });
      const fileHandle = await directory.getFileHandle(fileName, { create: true });
      const writable = await fileHandle.createWritable();

      try {
        await writable.write(toJsonl(records));
      } finally {
        await writable.close();
      }

      return {
        fileName,
        relativePath: `${IMPORT_DIRECTORY.join("/")}/${fileName}`,
      };
    }

    return {
      OFFER_ORIGIN,
      IMPORT_DIRECTORY,
      isOfferSiteUrl,
      buildImportFileName,
      createExportRecords,
      toJsonl,
      writeImportFile,
    };
  }
);
