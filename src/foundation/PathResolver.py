from pathlib import Path
import traceback
from typing import List

from ..primitives.PathInfo import PathInfo 

"""
PathResolver is a utility class to resolve the caller's path and determine
if the caller can escalate to admin level based on the path structure.
It traverses the stack trace to find the caller's frame and checks if the
caller can escalate to admin level based on the path type.
"""
class PathResolver:
    def __init__(self, base_paths: List[str] | str):
        """
        PathResolverの初期化
        base_pathsには単一のパスまたは複数のベースパスを指定可能
        """
        if isinstance(base_paths, str):
            base_paths = [base_paths]
        
        if not base_paths or any(not path for path in base_paths):
            raise ValueError("Base paths cannot be empty.")

        self.base_paths = [Path(path).resolve() for path in base_paths]
        
        # 各ベースパスのディレクトリを作成
        for base_path in self.base_paths:
            base_path.mkdir(parents=True, exist_ok=True)
        
        # 主要なベースパスを使用してtypeを決定（最初のパス）
        primary_base = self.base_paths[0]
        self.type = primary_base.parts[-1].lower() if 0 < len(primary_base.parts) else "unknown"

    def getPathInfo(self) -> PathInfo:
        """
        Traverse the stack trace to find the caller's frame.
        複数のベースパスに対して相対パス解決を試行
        (container directory)/(caller name)/**/*
        '-1' to exclude PathResolver itself
        'reversed' so that the caller can only get itself
        """
        stacks = traceback.extract_stack()

        if not stacks:
            raise ValueError("No stack frames found.")

        for stack in reversed(stacks[:-1]):
            stack_path = Path(stack.filename).resolve()

            # 複数のベースパスに対して相対パス解決を試行
            # 最も具体的（深い階層）なマッチを見つけるため、すべてのベースパスをチェック
            matched_paths = []
            
            for base_path in self.base_paths:
                try:
                    relative_path = stack_path.relative_to(base_path)
                    parts = relative_path.parts

                    if 0 < len(parts):
                        # ベースパスのタイプを動的に決定
                        base_type = base_path.parts[-1].lower() if 0 < len(base_path.parts) else "unknown"
                        
                        matched_paths.append({
                            'base_path': base_path,
                            'relative_path': relative_path,
                            'parts': parts,
                            'base_type': base_type,
                            'depth': len(base_path.parts)
                        })

                except ValueError:
                    # このベースパスでは解決できない、次のベースパスを試行
                    continue
            
            # マッチした中で最も深い階層（具体的）なベースパスを選択
            if matched_paths:
                # 深い階層順にソート（より具体的なパスを優先）
                matched_paths.sort(key=lambda x: x['depth'], reverse=True)
                best_match = matched_paths[0]
                
                return PathInfo(
                    name = best_match['parts'][0],
                    path = stack_path,
                    type = best_match['base_type']
                )

        raise ValueError("Caller name could not be determined.")
