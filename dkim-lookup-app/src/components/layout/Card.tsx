import type { ElementType, FC, ReactNode } from 'react';

interface CardProps {
	children: ReactNode;
	as?: ElementType;
}

export const Card: FC<CardProps> = ({ children, as: Tag = 'div' }) => {
	return (
		<Tag className={'rounded-xl border border-gray-300 bg-white p-4 m-4'}>
			{children}
		</Tag>
	);
};
