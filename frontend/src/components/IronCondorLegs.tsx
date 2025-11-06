import React from 'react';
import { IronCondorBuild } from '../api';

interface IronCondorLegsProps {
  build: IronCondorBuild;
}

export const IronCondorLegs: React.FC<IronCondorLegsProps> = ({ build }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Organize legs: [sell put, buy put, buy call, sell call]
  const sellPut = build.legs.find(leg => leg.side === 'sell' && leg.type === 'put');
  const buyPut = build.legs.find(leg => leg.side === 'buy' && leg.type === 'put');
  const buyCall = build.legs.find(leg => leg.side === 'buy' && leg.type === 'call');
  const sellCall = build.legs.find(leg => leg.side === 'sell' && leg.type === 'call');

  return (
    <div className="space-y-4">
      {/* 4-Leg Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Sell Put - Pink */}
        {sellPut && (
          <div className="bg-[#FCE4EC] rounded-2xl border-2 border-black p-5 md:p-6 shadow-md min-w-0">
            <p className="text-sm md:text-base text-gray-600 mb-2 truncate">
              Sell Put
            </p>
            <p className="text-2xl md:text-3xl font-mono font-bold text-black">
              ${sellPut.strike}
            </p>
            {sellPut.premium !== undefined && (
              <p className="text-xs text-gray-600 mt-1">
                {formatCurrency(sellPut.premium)} credit
              </p>
            )}
          </div>
        )}

        {/* Buy Put - Blue */}
        {buyPut && (
          <div className="bg-[#E3F2FD] rounded-2xl border-2 border-black p-5 md:p-6 shadow-md min-w-0">
            <p className="text-sm md:text-base text-gray-600 mb-2 truncate">
              Buy Put
            </p>
            <p className="text-2xl md:text-3xl font-mono font-bold text-black">
              ${buyPut.strike}
            </p>
            {buyPut.premium !== undefined && (
              <p className="text-xs text-gray-600 mt-1">
                {formatCurrency(buyPut.premium)} debit
              </p>
            )}
          </div>
        )}

        {/* Buy Call - Blue */}
        {buyCall && (
          <div className="bg-[#E3F2FD] rounded-2xl border-2 border-black p-5 md:p-6 shadow-md min-w-0">
            <p className="text-sm md:text-base text-gray-600 mb-2 truncate">
              Buy Call
            </p>
            <p className="text-2xl md:text-3xl font-mono font-bold text-black">
              ${buyCall.strike}
            </p>
            {buyCall.premium !== undefined && (
              <p className="text-xs text-gray-600 mt-1">
                {formatCurrency(buyCall.premium)} debit
              </p>
            )}
          </div>
        )}

        {/* Sell Call - Pink */}
        {sellCall && (
          <div className="bg-[#FCE4EC] rounded-2xl border-2 border-black p-5 md:p-6 shadow-md min-w-0">
            <p className="text-sm md:text-base text-gray-600 mb-2 truncate">
              Sell Call
            </p>
            <p className="text-2xl md:text-3xl font-mono font-bold text-black">
              ${sellCall.strike}
            </p>
            {sellCall.premium !== undefined && (
              <p className="text-xs text-gray-600 mt-1">
                {formatCurrency(sellCall.premium)} credit
              </p>
            )}
          </div>
        )}
      </div>

      {/* Risk Summary */}
      <div className="bg-white rounded-2xl border-2 border-black p-6 shadow-md">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="min-w-0">
            <p className="text-sm text-gray-600 mb-1 truncate">Net Credit</p>
            <p className="text-xl md:text-2xl font-mono font-bold text-emerald">
              +{formatCurrency(build.net_credit)}
            </p>
          </div>
          <div className="min-w-0">
            <p className="text-sm text-gray-600 mb-1 truncate">Max Loss</p>
            <p className="text-xl md:text-2xl font-mono font-bold text-rose">
              {formatCurrency(build.max_loss)}
            </p>
          </div>
          <div className="min-w-0">
            <p className="text-sm text-gray-600 mb-1 truncate">Spread Width</p>
            <p className="text-xl md:text-2xl font-mono font-bold text-black">
              ${build.spread_width}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IronCondorLegs;
